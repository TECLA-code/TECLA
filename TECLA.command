#!/bin/bash
cd "$(dirname "$0")/codi"
echo ""
echo "  ╔══════════════════════════╗"
echo "  ║     T E C L A  Web       ║"
echo "  ╚══════════════════════════╝"
echo ""
python3 server.py &
SERVER_PID=$!
sleep 1
open "http://localhost:8080/tecla.html"
echo "  Servidor actiu (PID $SERVER_PID)"
echo "  Tanca aquesta finestra per aturar-lo."
echo ""
wait $SERVER_PID
