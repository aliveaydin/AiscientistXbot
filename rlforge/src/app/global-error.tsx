"use client";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, backgroundColor: "#000", color: "#fff", fontFamily: "system-ui, sans-serif" }}>
        <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: "1rem" }}>
          <div style={{ textAlign: "center", maxWidth: "400px" }}>
            <div style={{ fontSize: "40px", marginBottom: "16px" }}>
              &#9888;
            </div>
            <h2 style={{ fontSize: "18px", fontWeight: 600, marginBottom: "8px" }}>
              Something went wrong
            </h2>
            <p style={{ fontSize: "14px", color: "#888", marginBottom: "24px", lineHeight: 1.6 }}>
              {error.message || "An unexpected error occurred. Please try again."}
            </p>
            <div style={{ display: "flex", gap: "12px", justifyContent: "center" }}>
              <button
                onClick={reset}
                style={{
                  padding: "10px 20px",
                  backgroundColor: "#fff",
                  color: "#000",
                  border: "none",
                  borderRadius: "6px",
                  fontSize: "14px",
                  fontWeight: 600,
                  cursor: "pointer",
                }}
              >
                Try Again
              </button>
              <a
                href="/"
                style={{
                  padding: "10px 20px",
                  border: "1px solid #333",
                  color: "#888",
                  borderRadius: "6px",
                  fontSize: "14px",
                  textDecoration: "none",
                }}
              >
                Go Home
              </a>
            </div>
            {error.digest && (
              <p style={{ fontSize: "10px", color: "#444", marginTop: "16px", fontFamily: "monospace" }}>
                Error ID: {error.digest}
              </p>
            )}
          </div>
        </div>
      </body>
    </html>
  );
}
