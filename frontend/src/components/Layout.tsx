import { Navbar, NavbarActions, NavbarBrand, NavbarContainer } from "ice-ds";
import { AudioLines } from "lucide-react";
import type { ReactNode } from "react";
import { useNavigate } from "react-router-dom";

import { AccountMenu } from "@/features/auth/components/AccountMenu";

export function Layout({ children }: { children: ReactNode }) {
  const navigate = useNavigate();

  return (
    <div className="flex min-h-screen flex-col">
      <Navbar variant="yellow">
        <NavbarContainer>
          <NavbarBrand
            href="/"
            onClick={(event) => {
              event.preventDefault();
              navigate("/");
            }}
            className="flex items-center gap-2"
          >
            <AudioLines className="h-6 w-6" strokeWidth={2.75} /> Tala
          </NavbarBrand>
          <NavbarActions>
            <AccountMenu />
          </NavbarActions>
        </NavbarContainer>
      </Navbar>
      <main className="mx-auto w-full max-w-3xl flex-1 px-4 py-10 sm:py-14">{children}</main>
      <footer className="border-t-[3px] border-neo-black bg-neo-black px-4 py-6 text-sm text-neo-offwhite">
        <div className="mx-auto max-w-3xl">
          Built for Paolo. Runs on open-source Whisper — no signup needed, no cards, no tracking.
        </div>
      </footer>
    </div>
  );
}
