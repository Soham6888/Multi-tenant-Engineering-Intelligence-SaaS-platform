"""Test-only Redis protocol server. Never use this fake as an application dependency."""
from fakeredis import TcpFakeServer


if __name__ == "__main__":
    server = TcpFakeServer(("127.0.0.1", 55433))
    print("TEST ONLY: Fakeredis on loopback 127.0.0.1:55433", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    finally:
        server.server_close()
