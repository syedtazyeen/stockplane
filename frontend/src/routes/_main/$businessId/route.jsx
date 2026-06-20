import {
  createFileRoute,
  Outlet,
  redirect,
  useLocation,
} from "@tanstack/react-router";
import {
  HouseIcon,
  TagIcon,
  TrayIcon,
  UsersIcon,
} from "@phosphor-icons/react";

import { NotFound } from "@/components/shared/not-found";
import { AppShell } from "@/components/shell";
import { getMemberships } from "@/lib/auth-session";

export const Route = createFileRoute("/_main/$businessId")({
  notFoundComponent: NotFound,
  beforeLoad: ({ params }) => {
    const memberships = getMemberships();
    const membership = memberships.find(
      (item) => item.business.id === params.businessId,
    );

    if (!membership) {
      const fallbackBusinessId = memberships[0]?.business?.id;

      if (fallbackBusinessId) {
        throw redirect({
          to: "/$businessId/home",
          params: { businessId: fallbackBusinessId },
        });
      }

      throw redirect({ to: "/login" });
    }

    return { membership };
  },
  component: BusinessShell,
});

function buildMenuItems(businessId) {
  const prefix = `/${businessId}`;

  return {
    menuItems: [
      { label: "Home", icon: HouseIcon, href: `${prefix}/home` },
      {
        label: "Orders",
        icon: TrayIcon,
        href: `${prefix}/orders`,
        children: [{ label: "Draft", href: `${prefix}/draft_orders` }],
      },
      {
        label: "Products",
        icon: TagIcon,
        href: `${prefix}/products`,
        children: [{ label: "Inventory", href: `${prefix}/inventory` }],
      },
      { label: "Customers", icon: UsersIcon, href: `${prefix}/customers` },
    ],
    bottomMenuItems: [],
  };
}

function isActive(pathname, href) {
  return pathname === href || pathname.startsWith(`${href}/`);
}

function isGroupOpen(pathname, item) {
  const triggerActive = item.href ? isActive(pathname, item.href) : false;
  const childActive = item.children.some((child) =>
    isActive(pathname, child.href),
  );
  return triggerActive || childActive;
}

function BusinessShell() {
  const { businessId } = Route.useParams();
  const location = useLocation();
  const pathname = location.pathname;
  const { menuItems, bottomMenuItems } = buildMenuItems(businessId);

  return (
    <AppShell>
      <AppShell.Header />
      <AppShell.Sidebar>
        <AppShell.Sidebar.Group>
          {menuItems.map((item) =>
            item.children ? (
              <AppShell.Sidebar.SubGroup
                key={item.label}
                open={isGroupOpen(pathname, item)}
              >
                <AppShell.Sidebar.SubTrigger
                  icon={item.icon}
                  label={item.label}
                  href={item.href}
                  active={item.href ? isActive(pathname, item.href) : false}
                />
                {item.children.map((child) => (
                  <AppShell.Sidebar.SubItem
                    key={child.href}
                    href={child.href}
                    label={child.label}
                    active={isActive(pathname, child.href)}
                  />
                ))}
              </AppShell.Sidebar.SubGroup>
            ) : (
              <AppShell.Sidebar.GroupItem
                key={item.href}
                icon={item.icon}
                label={item.label}
                href={item.href}
                active={isActive(pathname, item.href)}
              />
            ),
          )}
        </AppShell.Sidebar.Group>
        {bottomMenuItems.length > 0 ? (
          <AppShell.Sidebar.BottomGroup>
            {bottomMenuItems.map((item) => (
              <AppShell.Sidebar.BottomGroupItem
                key={item.href}
                icon={item.icon}
                label={item.label}
                href={item.href}
                active={isActive(pathname, item.href)}
              />
            ))}
          </AppShell.Sidebar.BottomGroup>
        ) : null}
      </AppShell.Sidebar>
      <AppShell.Main>
        <AppShell.Content>
          <Outlet />
        </AppShell.Content>
      </AppShell.Main>
    </AppShell>
  );
}
