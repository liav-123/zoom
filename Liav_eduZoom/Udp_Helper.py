import math


class UDP_Helper:
    @staticmethod
    def send_frame_to_server(sock, frame_data, server_address, frame_id, max_chunk_size=1400):
        """
        Splits data into chunks and sends them over UDP with a header.

        :param sock: The bound socket object
        :param frame_data: The bytes to send (e.g., JPEG buffer)
        :param server_address: (ip, port) tuple
        :param frame_id: An integer (0-255) to identify the current frame
        :param max_chunk_size: Size of the payload per packet
        """
        data_size = len(frame_data)
        total_chunks = math.ceil(data_size / max_chunk_size)

        if total_chunks > 255:
            print("Warning: Data too large for 1-byte chunk index. Increase max_chunk_size or decrease resolution.")
            return

        for i in range(total_chunks):
            start = i * max_chunk_size
            end = min(start + max_chunk_size, data_size)

            # Build Header: [Frame ID][Total Chunks][Chunk Index][Padding]
            header = bytes([frame_id % 256, total_chunks, i, 0])
            payload = header + frame_data[start:end]

            sock.sendto(payload, server_address)

    @staticmethod
    def receive_and_reassemble(udp_sock,frame_buffer, buffer_size=65535):
        """
        Listens for UDP packets, extracts headers, and reassembles frames.
        Returns the raw bytes of a full frame once all chunks are collected.
        """
        try:
            packet, addr = udp_sock.recvfrom(buffer_size)

            # 1. Extract Header (First 4 bytes)
            # [0]: frame_id, [1]: total_chunks, [2]: chunk_index
            frame_id = packet[0]
            total_chunks = packet[1]
            chunk_index = packet[2]
            payload = packet[4:]  # The actual image data

            # 2. Store the chunk
            # We store as (index, data) so we can sort them later
            frame_buffer[frame_id].append((chunk_index, payload))

            # 3. Check if frame is complete
            if len(frame_buffer[frame_id]) == total_chunks:
                # Sort by chunk index to ensure correct order
                sorted_chunks = sorted(frame_buffer[frame_id], key=lambda x: x[0])

                # Combine all payloads into one byte string
                full_frame_data = b"".join([c[1] for c in sorted_chunks])

                # Cleanup: Remove this frame from buffer to save memory
                del frame_buffer[frame_id]

                return full_frame_data, addr

        except Exception as e:
            print(f"Error receiving: {e}")

        return None, None