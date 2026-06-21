import {
  useEffect,
  useRef,
} from "react";

import type { ChatMessage } from "../../types";

import { LoadingSpinner } from "../shared/LoadingSpinner";
import { ChatMessage as ChatMessageBubble } from "./ChatMessage";

interface ChatWindowProps {
  messages: ChatMessage[];
  isSending: boolean;
}

export function ChatWindow({
  messages,
  isSending,
}: ChatWindowProps) {
  const bottomReference =
    useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    bottomReference.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, isSending]);

  return (
    <div
      className={[
        "h-[430px] overflow-y-auto",
        "bg-slate-50 px-4 py-5",
        "sm:px-6",
      ].join(" ")}
      aria-live="polite"
    >
      {messages.length === 0 ? (
        <div className="flex h-full items-center justify-center">
          <div className="max-w-sm text-center">
            <div
              className={[
                "mx-auto flex h-14 w-14",
                "items-center justify-center",
                "rounded-2xl bg-blue-100",
                "text-xl font-black text-blue-700",
              ].join(" ")}
              aria-hidden="true"
            >
              AI
            </div>

            <h2 className="mt-4 text-lg font-black text-slate-900">
              Start a refund conversation
            </h2>

            <p className="mt-2 text-sm leading-6 text-slate-500">
              Select a demo customer, choose an order if
              available, and describe why the customer wants a
              refund.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-4">
          {messages.map((message) => (
            <ChatMessageBubble
              key={message.id}
              message={message}
            />
          ))}

          {isSending ? (
            <div className="flex justify-start">
              <div
                className={[
                  "rounded-2xl rounded-bl-md",
                  "border border-slate-200",
                  "bg-white px-4 py-3",
                  "text-sm text-slate-600 shadow-sm",
                ].join(" ")}
              >
                <LoadingSpinner
                  label="Agent is checking the policy"
                  size="small"
                />
              </div>
            </div>
          ) : null}
        </div>
      )}

      <div ref={bottomReference} />
    </div>
  );
}