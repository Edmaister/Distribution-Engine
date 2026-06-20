import { CircleAlert } from "lucide-react";
import { ApiError } from "../api/client";

export function ErrorPanel({ error }: { error: unknown }) {
  const apiError = normalizeError(error);

  return (
    <div className="banner danger">
      <CircleAlert size={18} />
      <div>
        <strong>{apiError.status ? `Status ${apiError.status}` : "Request error"}</strong>
        <div className="muted">{apiError.message}</div>
      </div>
    </div>
  );
}

function normalizeError(error: unknown): Partial<ApiError> & { message: string } {
  if (typeof error === "string") {
    return { message: error };
  }

  if (error instanceof Error) {
    return { message: error.message };
  }

  if (error && typeof error === "object") {
    const apiError = error as Partial<ApiError>;
    return {
      status: apiError.status,
      message: apiError.message || "The request could not be completed.",
      details: apiError.details,
    };
  }

  return { message: "The request could not be completed." };
}
