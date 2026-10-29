function renderInline(text: string) {
  const parts = text.split(/(`[^`]+`|\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith("`") && part.endsWith("`")) {
      return <code key={i}>{part.slice(1, -1)}</code>;
    }
    if (part.startsWith("**") && part.endsWith("**")) {
      return <strong key={i}>{part.slice(2, -2)}</strong>;
    }
    return <span key={i}>{part}</span>;
  });
}

export function Prose({ text }: { text: string }) {
  const blocks = text.split(/\n\n+/);
  return (
    <div className="grd-prose">
      {blocks.map((block, i) => {
        if (block.startsWith("```")) {
          const inner = block.replace(/^```[a-z]*\n?/, "").replace(/```$/, "");
          return (
            <pre key={i}>
              <code>{inner}</code>
            </pre>
          );
        }
        if (block.split("\n").every((l) => l.startsWith("- "))) {
          return (
            <ul key={i}>
              {block.split("\n").map((l, j) => (
                <li key={j}>{renderInline(l.slice(2))}</li>
              ))}
            </ul>
          );
        }
        return <p key={i}>{renderInline(block)}</p>;
      })}
    </div>
  );
}
