import errno
import sys


def read_all(socket, buffer_size):
    totalData = []
    data = socket.recv(buffer_size)
    while data:
        totalData.append(data)
        try:
            data = socket.recv(buffer_size)
        except IOError as e:
            if e.errno == errno.EWOULDBLOCK:
                break
            else:
                raise
    return ''.join(totalData)

