import { ListIcon, SignOutIcon } from "@phosphor-icons/react";
import { useParams } from "@tanstack/react-router";

import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuGroup,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Logo } from "@/components/shared/logo";
import { useAuth, useLogout } from "@/hooks/use-auth";
import { getMemberships } from "@/lib/auth-session";

import { useAppShell } from "./context";

function getBusinessInitials(business) {
  if (business?.name) {
    return business.name
      .split(" ")
      .map((part) => part[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();
  }

  return "B";
}

function getUserInitials(user) {
  if (user?.full_name) {
    return user.full_name
      .split(" ")
      .map((part) => part[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();
  }

  return user?.email?.slice(0, 2).toUpperCase() ?? "U";
}

function getCurrentBusiness(businessId) {
  const memberships = getMemberships();
  const membership = memberships.find(
    (item) => item.business.id === businessId,
  );

  return membership?.business ?? memberships[0]?.business ?? null;
}

function UserDropdown() {
  const { data: user } = useAuth();
  const logout = useLogout();
  const { businessId } = useParams({ strict: false });
  const business = getCurrentBusiness(businessId);
  const displayName = business?.name ?? "Business";

  return (
    <DropdownMenu>
      <DropdownMenuTrigger
        render={
          <Button
            variant="header-ghost"
            size="lg"
            className="w-fit max-w-40 pl-0.5 pr-0.5 md:pr-2.5"
          />
        }
      >
        <Avatar>
          <AvatarFallback className="rounded-lg">
            {getBusinessInitials(business)}
          </AvatarFallback>
        </Avatar>
        <span className="hidden truncate text-sm whitespace-nowrap text-header-foreground/70 md:block">
          {displayName}
        </span>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" sideOffset={16} alignOffset={-8} className="min-w-52">
        <DropdownMenuGroup>
          <div className="flex items-center gap-2 px-1.5 py-2">
            <Avatar>
              <AvatarFallback>{getUserInitials(user)}</AvatarFallback>
            </Avatar>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-foreground">
                {user?.full_name || "Account"}
              </p>
              <p className="truncate text-xs text-muted-foreground">
                {user?.email ?? "Signed in"}
              </p>
            </div>
          </div>
          <DropdownMenuSeparator />
          <DropdownMenuItem onClick={logout}>
            <SignOutIcon />
            Logout
          </DropdownMenuItem>
        </DropdownMenuGroup>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function Header() {
  const { sidebarOpen, toggleSidebar } = useAppShell();

  return (
    <header className="z-20 col-span-1 flex h-header-height items-center justify-between bg-header px-2 text-header-foreground md:col-span-2 md:px-4">
      <div className="flex items-center">
        <Button
          type="button"
          variant="header"
          size="icon-lg"
          className="md:hidden"
          aria-expanded={sidebarOpen}
          aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
          onClick={toggleSidebar}
        >
          <ListIcon />
        </Button>
        <Logo className="hidden md:block" />
      </div>

      <UserDropdown />
    </header>
  );
}
