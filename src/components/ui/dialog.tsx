// SPDX-License-Identifier: AGPL-3.0-only
/**
 * Minimaler Dialog-Stub.
 *
 * Der volle shadcn-Dialog basiert auf `@radix-ui/react-dialog`. Um die
 * Scaffold-Phase schlank zu halten, bauen wir hier einen leichten
 * HTMLDialogElement-Wrapper. Welle-2-Agents koennen jederzeit das echte
 * Radix-Setup via `pnpm dlx shadcn@latest add dialog` nachziehen.
 */
import * as React from "react";
import { cn } from "@/lib/utils";

export interface DialogProps extends React.HTMLAttributes<HTMLDivElement> {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function Dialog({
  open,
  onOpenChange,
  className,
  children,
  ...props
}: DialogProps) {
  if (!open) return null;
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={() => onOpenChange(false)}
    >
      <div
        className={cn(
          "max-w-lg rounded-lg border bg-background p-6 shadow-lg",
          className,
        )}
        onClick={(e) => e.stopPropagation()}
        {...props}
      >
        {children}
      </div>
    </div>
  );
}

export function DialogHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn("mb-4 flex flex-col space-y-1.5", className)}
      {...props}
    />
  );
}

export function DialogTitle({
  className,
  ...props
}: React.HTMLAttributes<HTMLHeadingElement>) {
  return (
    <h2
      className={cn("text-lg font-semibold leading-none", className)}
      {...props}
    />
  );
}

export function DialogDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p className={cn("text-sm text-muted-foreground", className)} {...props} />
  );
}
