import type { ReactNode } from "react";

type Props = {
  title: string;
  description: string;
  action?: ReactNode;
};

export function PageHeader({ title, description, action }: Props) {
  return (
    <header className="grd-page-header">
      <div>
        <div className="grd-page-header-title">
          <h1>{title}</h1>
          {action}
        </div>
        <p>{description}</p>
      </div>
    </header>
  );
}
