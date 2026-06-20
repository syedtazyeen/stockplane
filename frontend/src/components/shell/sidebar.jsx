import { Button as ButtonBase } from "@base-ui/react";
import { Collapsible } from "@base-ui/react/collapsible";
import { Link } from "@tanstack/react-router";
import { ArrowBendDownRightIcon } from "@phosphor-icons/react";
import { Children, cloneElement, isValidElement, useState } from "react";

import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";

import { useAppShell } from "./context";

const itemClassName =
  "flex items-center gap-2 w-full justify-start rounded-lg px-2.5 h-7 text-sm font-medium leading-6 text-sidebar-foreground hover:bg-sidebar-primary/50 data-active:bg-sidebar-primary hover:data-active:bg-sidebar-primary data-active:text-sidebar-primary-foreground";

function MenuGroup({ children, className, ...props }) {
  return (
    <div className={cn("flex flex-col gap-px", className)} {...props}>
      {children}
    </div>
  );
}

function MenuItem({
  className,
  active = false,
  icon: Icon = null,
  label,
  href,
  onClick,
  ...props
}) {
  const { closeSidebar } = useAppShell();

  return (
    <ButtonBase
      role="button"
      data-slot="sidebar-item"
      data-active={active || undefined}
      className={cn(itemClassName, className)}
      render={href ? <Link to={href} /> : null}
      onClick={(event) => {
        closeSidebar();
        onClick?.(event);
      }}
      {...props}
    >
      {Icon && <Icon className="size-4" weight={active ? "regular" : "fill"} />}
      {label}
    </ButtonBase>
  );
}

function MenuSubGroup({
  children,
  className,
  open: forceOpen = false,
  defaultOpen = false,
  ...props
}) {
  const [userOpen, setUserOpen] = useState(defaultOpen);
  const isOpen = forceOpen || userOpen;
  let trigger = null;
  const items = [];

  Children.forEach(children, (child) => {
    if (isValidElement(child) && child.type === MenuSubTrigger) {
      trigger = cloneElement(child, { expanded: isOpen });
      return;
    }

    items.push(child);
  });

  return (
    <Collapsible.Root
      open={isOpen}
      onOpenChange={(nextOpen) => {
        if (!forceOpen) {
          setUserOpen(nextOpen);
        }
      }}
      className={cn("flex flex-col gap-px", className)}
      {...props}
    >
      {trigger}
      <Collapsible.Panel
        data-slot="sidebar-sub-panel"
        className="flex flex-col gap-px"
      >
        <div className="mb-2 flex flex-col gap-px">{items}</div>
      </Collapsible.Panel>
    </Collapsible.Root>
  );
}

function MenuSubTrigger({
  className,
  active = false,
  expanded = false,
  icon: Icon = null,
  label,
  href,
  onClick,
  ...props
}) {
  const { closeSidebar } = useAppShell();
  const iconWeight = active || expanded ? "regular" : "fill";

  if (!href) {
    return (
      <Collapsible.Trigger
        data-slot="sidebar-sub-trigger"
        data-active={active || undefined}
        className={cn(itemClassName, className)}
        {...props}
      >
        {Icon && <Icon className="size-4" weight={iconWeight} />}
        <span className="flex-1 text-left">{label}</span>
      </Collapsible.Trigger>
    );
  }

  return (
    <div
      data-slot="sidebar-sub-trigger"
      data-active={active || undefined}
      className={cn(itemClassName, "gap-0 p-0", className)}
    >
      <ButtonBase
        className="flex h-7 min-w-0 flex-1 items-center gap-2 rounded-lg px-2.5 text-inherit hover:bg-transparent data-active:bg-transparent"
        render={<Link to={href} />}
        onClick={(event) => {
          closeSidebar();
          onClick?.(event);
        }}
      >
        {Icon && <Icon className="size-4" weight={iconWeight} />}
        <span className="flex-1 truncate text-left">{label}</span>
      </ButtonBase>
      <Collapsible.Trigger
        className="flex size-7 shrink-0 items-center justify-center rounded-lg text-inherit hover:bg-sidebar-primary hover:text-sidebar-primary-foreground"
        {...props}
      />
    </div>
  );
}

function MenuSubItem({
  className,
  active = false,
  label,
  href,
  onClick,
  ...props
}) {
  const { closeSidebar } = useAppShell();

  return (
    <ButtonBase
      role="button"
      data-slot="sidebar-sub-item"
      data-active={active || undefined}
      className={cn(
        itemClassName,
        "group/sub-item opacity-80 data-active:opacity-100",
        className,
      )}
      render={href ? <Link to={href} /> : null}
      onClick={(event) => {
        closeSidebar();
        onClick?.(event);
      }}
      {...props}
    >
      <ArrowBendDownRightIcon
        className={cn(
          "size-4 shrink-0 transition-opacity",
          active ? "opacity-100" : "opacity-0 group-hover/sub-item:opacity-40",
        )}
        weight={active ? "regular" : "fill"}
      />
      {label}
    </ButtonBase>
  );
}

function BottomGroup({ children, className, ...props }) {
  return (
    <div className={cn("flex flex-col gap-px", className)} {...props}>
      {children}
    </div>
  );
}

function Sidebar({ children }) {
  const { sidebarOpen, closeSidebar } = useAppShell();

  const childArray = Children.toArray(children);
  const bottomGroups = childArray.filter(
    (child) => isValidElement(child) && child.type === BottomGroup,
  );
  const mainChildren = childArray.filter(
    (child) => !isValidElement(child) || child.type !== BottomGroup,
  );

  return (
    <>
      <div
        aria-hidden={!sidebarOpen}
        className={cn(
          "fixed inset-0 top-header-height z-40 bg-black/50 transition-opacity md:hidden",
          sidebarOpen ? "opacity-100" : "pointer-events-none opacity-0",
        )}
        onClick={closeSidebar}
      />

      <aside className="row-start-2 h-full min-h-0 max-md:contents">
        <div
          className={cn(
            "h-full w-full bg-sidebar",
            "md:relative md:rounded-tl-2xl",
            "max-md:fixed max-md:top-header-height max-md:bottom-0 max-md:left-0 max-md:z-50 max-md:w-sidebar-width",
            "max-md:rounded-r-2xl max-md:shadow-lg",
            "max-md:transition-transform max-md:duration-300 max-md:ease-in-out",
            sidebarOpen ? "max-md:translate-x-0" : "max-md:-translate-x-full",
          )}
        >
          <div className="flex size-full flex-col rounded-[inherit] md:rounded-tl-2xl max-md:rounded-r-2xl">
            <ScrollArea className="h-0 min-h-0 flex-1">
              <div className="space-y-px px-3.5 py-3">{mainChildren}</div>
            </ScrollArea>

            {bottomGroups.length > 0 && (
              <div className="shrink-0 space-y-px px-3.5 py-3">
                {bottomGroups}
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  );
}

Sidebar.Group = MenuGroup;
Sidebar.GroupItem = MenuItem;
Sidebar.SubGroup = MenuSubGroup;
Sidebar.SubTrigger = MenuSubTrigger;
Sidebar.SubItem = MenuSubItem;
Sidebar.BottomGroup = BottomGroup;
Sidebar.BottomGroupItem = MenuItem;

export { Sidebar };
