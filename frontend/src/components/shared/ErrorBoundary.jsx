import React from "react";
import { AlertTriangle } from "lucide-react";

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    // eslint-disable-next-line no-console
    console.error("UI error boundary caught:", error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="page">
          <div className="card card-pad">
            <div className="alert alert-danger">
              <AlertTriangle size={18} />
              <div>
                <div className="font-semibold">Something went wrong</div>
                <div className="text-sm mt-2">
                  {this.state.error?.message || "An unexpected error occurred."}
                </div>
              </div>
            </div>
            <button
              className="btn btn-secondary mt-4"
              onClick={() => window.location.reload()}
            >
              Reload page
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
