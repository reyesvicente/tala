import { Button, EmptyState } from "ice-ds";
import { Link } from "react-router-dom";

export default function NotFoundPage() {
  return (
    <EmptyState
      title="Nothing here"
      description="That page doesn't exist."
      action={
        <Link to="/">
          <Button type="button">Go home</Button>
        </Link>
      }
    />
  );
}
