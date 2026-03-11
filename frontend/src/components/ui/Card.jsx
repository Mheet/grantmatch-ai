export default function Card({
  children,
  className = "",
  padding = "p-6",
  hover = false,
  ...props
}) {
  return (
    <div
      className={`
        bg-white rounded-xl border border-slate-200
        shadow-sm
        ${hover ? "hover:shadow-md hover:border-slate-300 transition-shadow duration-200" : ""}
        ${padding}
        ${className}
      `}
      {...props}
    >
      {children}
    </div>
  );
}

Card.Header = function CardHeader({ children, className = "" }) {
  return (
    <div className={`mb-4 ${className}`}>
      {children}
    </div>
  );
};

Card.Title = function CardTitle({ children, className = "" }) {
  return (
    <h3 className={`text-lg font-semibold text-navy-900 ${className}`}>
      {children}
    </h3>
  );
};

Card.Description = function CardDescription({ children, className = "" }) {
  return (
    <p className={`text-sm text-slate-500 mt-1 ${className}`}>
      {children}
    </p>
  );
};

Card.Footer = function CardFooter({ children, className = "" }) {
  return (
    <div className={`mt-4 pt-4 border-t border-slate-100 ${className}`}>
      {children}
    </div>
  );
};
