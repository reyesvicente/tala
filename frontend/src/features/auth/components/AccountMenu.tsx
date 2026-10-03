import { Button, buttonVariants } from "ice-ds";
import { LogOut } from "lucide-react";
import { Link } from "react-router-dom";

import { useLogout, useMe } from "../api";

export function AccountMenu() {
  const { data: user, isPending } = useMe();
  const logout = useLogout();

  if (isPending) return null;

  if (!user) {
    return (
      <div className="flex items-center gap-2">
        <Link to="/login" className={buttonVariants({ variant: "ghost", size: "sm" })}>
          Log in
        </Link>
        <Link to="/signup" className={buttonVariants({ variant: "inverse", size: "sm" })}>
          Sign up
        </Link>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2">
      <Link to="/history" className={buttonVariants({ variant: "ghost", size: "sm" })}>
        My transcripts
      </Link>
      <span className="hidden max-w-48 truncate text-sm md:inline" title={user.email}>
        {user.email}
      </span>
      <Button
        type="button"
        variant="secondary"
        size="sm"
        loading={logout.isPending}
        onClick={() => logout.mutate()}
      >
        <LogOut className="mr-1 h-4 w-4" /> Log out
      </Button>
    </div>
  );
}
