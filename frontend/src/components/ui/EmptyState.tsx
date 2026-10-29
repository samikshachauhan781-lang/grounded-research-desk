import type { ReactNode } from "react";

type Props = {
  title: string;
  body: string;
  action?: ReactNode;
};

export function EmptyState({ title, body, action }: Props) {
  return (
    <div className="grd-empty">
      <h3>{title}</h3>
      <p>{body}</p>
      {action ? <div style={{ marginTop: "1rem" }}>{action}</div> : null}
    </div>
  );
}
