import math


class UDP_Helper:
    @staticmethod
    def send_frame_to_server(sock, frame_data, server_address, frame_id, max_chunk_size=1400):
        # ... (Your existing send_frame_to_server logic remains exactly the same) ...
        data_size = len(frame_data)
        total_chunks = math.ceil(data_size / max_chunk_size)
        if total_chunks > 255: return
        for i in range(total_chunks):
            start = i * max_chunk_size
            end = min(start + max_chunk_size, data_size)
            header = bytes([frame_id % 256, total_chunks, i, 0])
            payload = header + frame_data[start:end]
            sock.sendto(payload, server_address)

    @staticmethod
    def receive_and_reassemble(udp_sock, frame_buffer, buffer_size=65535):
        try:
            packet, addr = udp_sock.recvfrom(buffer_size)
            if len(packet) < 4: return None, None

            frame_id = packet[0]
            total_chunks = packet[1]
            chunk_index = packet[2]
            payload = packet[4:]

            # PREVENT MEMORY LEAK: Limit buffer to hold max 5 frames at a time
            if len(frame_buffer) > 5:
                oldest_frame = list(frame_buffer.keys())[0]
                del frame_buffer[oldest_frame]

            frame_buffer[frame_id].append((chunk_index, payload))

            if len(frame_buffer[frame_id]) == total_chunks:
                sorted_chunks = sorted(frame_buffer[frame_id], key=lambda x: x[0])
                full_frame_data = b"".join([c[1] for c in sorted_chunks])
                del frame_buffer[frame_id]
                return full_frame_data, addr

        except Exception as e:
            pass
        return None, None