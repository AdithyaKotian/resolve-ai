import type { ChatMessage as ChatMessageType } from "../../types";

interface ChatMessageProps {
  message: ChatMessageType;
}

function formatTime(timestamp: string): string {
  return new Intl.DateTimeFormat("en-US", {
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(timestamp));
}

export function ChatMessage({
  message,
}: ChatMessageProps) {
  const isCustomer = message.role === "user";

  return (
    <article
      className={[
        "flex",
        isCustomer
          ? "justify-end"
          : "justify-start",
      ].join(" ")}
    >
      <div
        className={[
          "max-w-[88%] rounded-2xl px-4 py-3",
          "shadow-sm sm:max-w-[75%]",
          isCustomer
            ? "rounded-br-md bg-blue-600 text-white"
            : [
                "rounded-bl-md border",
                "border-slate-200",
                "bg-white text-slate-800",
              ].join(" "),
        ].join(" ")}
      >
        <p className="whitespace-pre-wrap text-sm leading-6">
          {message.content}
        </p>

        <p
          className={[
            "mt-2 text-right text-[11px]",
            isCustomer
              ? "text-blue-100"
              : "text-slate-400",
          ].join(" ")}
        >
          {formatTime(message.createdAt)}
        </p>
      </div>
    </article>
  );
}