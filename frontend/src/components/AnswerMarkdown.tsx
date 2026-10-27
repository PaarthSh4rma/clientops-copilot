import Markdown from "react-markdown";

export function AnswerMarkdown({ children }: { children: string }) {
  return (
    <div className="answer-markdown break-words text-sm leading-7 text-slate-300">
      <Markdown
        skipHtml
        disallowedElements={["img"]}
        components={{
          a: ({ href, children: label }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sky-300 underline"
            >
              {label}
            </a>
          ),
        }}
      >
        {children}
      </Markdown>
    </div>
  );
}
