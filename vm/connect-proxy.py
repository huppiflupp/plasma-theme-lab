#!/usr/bin/env python3
"""A tiny HTTPS (CONNECT) proxy for the test VMs, on the host's loopback.

The VMs have no route to the internet (Docker set the host's FORWARD
policy to DROP), and the libvirt firewall zone blocks ports on the host.
So a VM reaches this proxy through an SSH reverse tunnel:

    ./connect-proxy.py &                                   # 127.0.0.1:3128
    ssh $SSH_OPTS -R 3128:127.0.0.1:3128 root@<vm> 'https_proxy=http://127.0.0.1:3128 pacman -Syu'

Only the hosts in ALLOW (suffix match) are let through; everything else
gets 403. build-vm-artix.sh starts it for the installation (Artix's
dated package archive).

    connect-proxy.py [--port 3128] [--allow host ...]
"""
import argparse
import asyncio

ALLOW = ["archive.artixlinux.org"]


async def pipe(reader, writer):
    try:
        while data := await reader.read(65536):
            writer.write(data)
            await writer.drain()
    except (ConnectionError, asyncio.CancelledError):
        pass
    finally:
        writer.close()


async def handle(reader, writer, allow):
    try:
        head = await reader.readuntil(b"\r\n\r\n")
    except (asyncio.IncompleteReadError, asyncio.LimitOverrunError):
        writer.close()
        return
    method, target, *_ = head.split(b"\r\n")[0].decode("latin-1").split()
    host, _, port = target.rpartition(":")
    if method != "CONNECT" or not any(host == a or host.endswith("." + a) for a in allow):
        writer.write(b"HTTP/1.1 403 Forbidden\r\nContent-Length: 0\r\n\r\n")
        await writer.drain()
        writer.close()
        print(f"denied {method} {target}", flush=True)
        return
    try:
        up_r, up_w = await asyncio.open_connection(host, int(port or 443))
    except OSError as e:
        writer.write(b"HTTP/1.1 502 Bad Gateway\r\nContent-Length: 0\r\n\r\n")
        await writer.drain()
        writer.close()
        print(f"failed {target}: {e}", flush=True)
        return
    writer.write(b"HTTP/1.1 200 Connection established\r\n\r\n")
    await writer.drain()
    await asyncio.gather(pipe(reader, up_w), pipe(up_r, writer))


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=3128)
    ap.add_argument("--allow", nargs="*", default=ALLOW)
    args = ap.parse_args()
    server = await asyncio.start_server(lambda r, w: handle(r, w, args.allow), "127.0.0.1", args.port)
    print(f"proxy on 127.0.0.1:{args.port} for {', '.join(args.allow)}", flush=True)
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(main())
