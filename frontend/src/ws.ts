/**
 * WebSocket client for F.R.I.D.A.Y. server communication.
 */

export type MessageHandler = (msg: Record<string, unknown>) => void;

export interface FridaySocket {
  send(data: Record<string, unknown>): void;
  onMessage(handler: MessageHandler): void;
  close(): void;
  isConnected(): boolean;
}

export function createSocket(url: string): FridaySocket {
  let ws: WebSocket | null = null;
  let handlers: MessageHandler[] = [];
  let reconnectDelay = 1000;
  let closed = false;
  let connected = false;

  function connect() {
    if (closed) return;

    ws = new WebSocket(url);

    ws.onopen = () => {
      connected = true;
      reconnectDelay = 1000;
      console.log("[ws] connected");
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        for (const h of handlers) h(msg);
      } catch {
        console.warn("[ws] bad message", event.data);
      }
    };

    ws.onclose = () => {
      connected = false;
      if (!closed) {
        console.log(`[ws] reconnecting in ${reconnectDelay}ms`);
        setTimeout(connect, reconnectDelay);
        reconnectDelay = Math.min(reconnectDelay * 2, 30000);
      }
    };

    ws.onerror = (err) => {
      console.error("[ws] error", err);
      ws?.close();
    };
  }

  connect();

  return {
    send(data) {
      if (ws?.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(data));
      }
    },
    onMessage(handler) {
      handlers.push(handler);
    },
    close() {
      closed = true;
      ws?.close();
    },
    isConnected() {
      return connected;
    },
  };
}
