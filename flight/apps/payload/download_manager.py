"""
Payload File Download Manager

Handles the orchestration of file downloads from the payload:
- Manages transaction queue
- Processes batches of packets (32 packets per batch)
- Detects file completion
- Generates confirmation bitmaps
- Finalizes files to disk

Author: Hazcoper
"""

import os

from core import logger
from core.time_processor import TimeProcessor as TPM


class DownloadManager:
    """
    Manages the download of files from the payload via transactions.
    
    Assumptions:
    - First batch starts at packet 0
    - Each batch contains 32 packets
    - Packets received are tracked in transaction.missing_fragments
    - File complete when missing_fragments is empty
    """
    
    # Configuration constants
    BATCH_SIZE = 60                # packets per batch
    LISTEN_TIMEOUT =  3 #(BATCH_SIZE * 500 * 8) / 460800             # seconds per batch listen adding 5byte margin per packet
    SAVE_FOLDER = "sd"
    MAX_BATCH_RETRIES = 3
    
    def __init__(self):
        """Initialize the download manager"""
        self.transaction_queue = []      # List of (tid, transaction) tuples
        self.current_tid = None
        self.current_transaction = None
        self.current_batch_offset = 0
        self.batch_retry_count = 0
        self.current_batch_received_any = False
        self.state = "IDLE"              # IDLE, ACTIVE, COMPLETE, ERROR
        
    def add_transaction(self, tid, transaction):
        """
        Add a new transaction to the download queue.
        
        Args:
            tid: Transaction ID
            transaction: Transaction object
        """
        if self.has_transaction(tid):
            logger.info(f"[DOWNLOAD_MGR] Transaction tid={tid} already tracked. Skipping duplicate queue entry.")
            return

        self.transaction_queue.append((tid, transaction))
        logger.info(f"[DOWNLOAD_MGR] Added transaction tid={tid} to queue. Queue size: {len(self.transaction_queue)}")

    def has_transaction(self, tid):
        """Return True if tid is already active or queued."""
        if self.current_tid == tid:
            return True

        for queued_tid, _ in self.transaction_queue:
            if queued_tid == tid:
                return True

        return False
        
    def _start_next_transaction(self):
        """
        Start processing the next transaction in the queue.
        
        Returns:
            True if a transaction was started, False if queue is empty
        """
        if len(self.transaction_queue) == 0:
            self.state = "IDLE"
            self.current_tid = None
            self.current_transaction = None
            return False
        
        self.current_tid, self.current_transaction = self.transaction_queue.pop(0)
        self.current_batch_offset = 0
        self.batch_retry_count = 0
        self.current_batch_received_any = False
        self.state = "ACTIVE"
        logger.info(
            f"[DOWNLOAD_MGR] Starting download for tid={self.current_tid}, total_packets={self.current_transaction.number_of_packets}"
        )
        return True

    def note_fragment_received(self, fragment):
        """
        Mark that at least one fragment for the active batch has been received.
        """
        if self.current_transaction is None:
            logger.warning("[DOWNLOAD_MGR] No active transaction to mark fragment as received.")
            return

        if fragment.tid != self.current_tid:
            logger.warning(f"[DOWNLOAD_MGR] Fragment tid={fragment.tid} does not match current transaction tid={self.current_tid}.")
            return

        batch_end = self.current_batch_offset + self.BATCH_SIZE
        if self.current_batch_offset <= fragment.seq_number < batch_end:
            self.current_batch_received_any = True
        else:
            logger.warning(f"[DOWNLOAD_MGR] Fragment seq_number={fragment.seq_number} is outside the current batch window.")
    
    def has_active_file(self):
        """Check if there is an active download in progress or queued"""
        return self.state == "ACTIVE" or len(self.transaction_queue) > 0
    
    def is_file_complete(self, transaction=None):
        """
        Check if all packets have been received for the current (or specified) transaction.
        
        Args:
            transaction: Transaction to check (default: current transaction)
            
        Returns:
            True if all packets received (bitset indicates all received)
        """
        trans = transaction or self.current_transaction
        if trans is None or trans.number_of_packets is None:
            return False
        return trans._missing_fragments_count == 0
    
    def process_batch(self, uart_reader_callback):
        """
        Process one batch of packets:
        1. Listen for incoming packets via callback
        2. Save partial file
        3. Calculate confirmation bitmap
        
        Args:
            uart_reader_callback: Callable that processes UART data for LISTEN_TIMEOUT seconds
                                 Should be: PC.process_uart
        
        Returns:
            Tuple: (bitmap_high, bitmap_low) of confirmation bitmap
            Raises: Exception if no active transaction
        """
        if self.current_transaction is None:
            if not self._start_next_transaction():
                raise Exception("No active transaction and queue is empty")
        
        trans = self.current_transaction
        
        # Listen for packets in this batch window
        start_listen_time = TPM.time()
        while TPM.time() - start_listen_time < self.LISTEN_TIMEOUT:
            uart_reader_callback()

        if not self.current_batch_received_any:
            logger.info(
                f"[DOWNLOAD_MGR] No fragments received yet for tid={self.current_tid}, seq_offset={self.current_batch_offset}. Waiting before sending confirmation."
            )
            return None, None
        
        # Save partial file to disk
        trans.write_partial_file(self.SAVE_FOLDER)
        
        # Calculate bitmap for current batch window
        width = self._calculate_batch_width()
        bitmap = self._generate_batch_bitmap(width)
        
        bitmap_high = (bitmap >> 32) & 0xFFFFFFFF
        bitmap_low = bitmap & 0xFFFFFFFF
        
        logger.info(
            f"[DOWNLOAD_MGR] Batch processed: tid={self.current_tid}, seq_offset={self.current_batch_offset}, width={width}, bitmap=0x{bitmap:016X}, missing_frags={trans._missing_fragments_count}"
        )
        
        return bitmap_high, bitmap_low
    
    def _calculate_batch_width(self):
        """Calculate the number of packets in the current batch"""
        if self.current_transaction.number_of_packets is None:
            return self.BATCH_SIZE
        
        remaining = self.current_transaction.number_of_packets - self.current_batch_offset
        return min(self.BATCH_SIZE, remaining)
    
    def _generate_batch_bitmap(self, width):
        """
        Generate bitmap for current batch.
        
        Bit logic: 1 = missing, 0 = received
        MSB-first ordering within the window
        MEMORY NOTE: Uses bitset _is_missing() instead of set() to avoid temporary allocation
        
        Args:
            width: Number of bits in this batch window
            
        Returns:
            Bitmap as integer
        """
        trans = self.current_transaction
        bitmap = 0
        
        for i in range(width):
            seq_number = self.current_batch_offset + i
            if trans._is_missing(seq_number):
                bit_pos = (width - 1) - i
                bitmap |= (1 << bit_pos)
        
        return bitmap
    
    def advance_batch(self):
        """
        Advance to next batch window.
        
        Returns:
            True if more batches to process, False if file is complete
        """
        self.current_batch_offset += self.BATCH_SIZE
        self.batch_retry_count = 0
        self.current_batch_received_any = False
        
        if self.is_file_complete():
            logger.info(f"[DOWNLOAD_MGR] File complete for tid={self.current_tid}")
            return False
        
        if self.current_batch_offset >= self.current_transaction.number_of_packets:
            logger.info(f"[DOWNLOAD_MGR] All batches processed for tid={self.current_tid}")
            return False
        
        return True
    
    def finalize_file(self):
        """
        Finalize the current file:
        - Write final file to disk
        - Mark transaction SUCCESS
        
        Returns:
            True if successful, False if verification failed
        """
        if self.current_transaction is None:
            logger.error("[DOWNLOAD_MGR] No active transaction to finalize")
            return False
        
        trans = self.current_transaction

        if len(trans.fragment_dict) > 0:
            trans.write_partial_file(self.SAVE_FOLDER)

        file_path = self.SAVE_FOLDER.rstrip("/") + "/" + trans.file_path.lstrip("/")

        try:
            os.stat(file_path)
        except Exception as error:
            logger.error(f"[DOWNLOAD_MGR] Final file missing for tid={self.current_tid}: {error}")
            return False

        trans.change_state(6)
        logger.info(f"[DOWNLOAD_MGR] File finalized successfully for tid={self.current_tid}")
        return True
    
    def advance_to_next_file(self):
        """
        Move to the next transaction in the queue.
        
        Returns:
            True if new file started, False if queue is empty
        """
        logger.info(
            f"[DOWNLOAD_MGR] Advancing from tid={self.current_tid}. Queue size: {len(self.transaction_queue)}"
        )
        
        if self._start_next_transaction():
            return True
        
        self.state = "COMPLETE"
        return False
    
    def get_status(self):
        """
        Get current download status.
        
        Returns:
            Dictionary with status information
        """
        status = {
            'state': self.state,
            'has_active_file': self.has_active_file(),
            'current_tid': self.current_tid,
            'queue_size': len(self.transaction_queue),
            'batch_offset': self.current_batch_offset,
        }
        
        if self.current_transaction is not None:
            missing_count = self.current_transaction._missing_fragments_count
            status.update({
                'total_packets': self.current_transaction.number_of_packets,
                # MEMORY NOTE: use bitmap-backed counter to avoid allocating missing list
                'missing_fragments': missing_count,
                'received_packets': (self.current_transaction.number_of_packets - 
                                   missing_count) 
                                   if self.current_transaction.number_of_packets else 0,
                'is_complete': self.is_file_complete(),
            })
        
        return status
    
    def reset(self):
        """Reset the download manager to initial state"""
        self.transaction_queue = []
        self.current_tid = None
        self.current_transaction = None
        self.current_batch_offset = 0
        self.batch_retry_count = 0
        self.current_batch_received_any = False
        self.state = "IDLE"
        logger.info("[DOWNLOAD_MGR] Download manager reset")
