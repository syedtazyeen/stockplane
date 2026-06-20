export function Main({ children }) {
  return (
    <div className="col-start-1 row-start-2 flex h-full min-h-0 flex-col overflow-hidden rounded-t-2xl bg-background md:col-start-2 md:rounded-tl-none md:rounded-tr-2xl">
      {children}
    </div>
  );
}
