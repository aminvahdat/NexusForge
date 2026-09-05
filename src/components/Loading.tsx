import React from "react";

interface Props {
  message: string;
}

const Loading: React.FC<Props> = ({ message }) => (
  <div className="flex items-center justify-center p-8">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
    <span className="ml-3 text-gray-600">{message}</span>
  </div>
);

export default Loading;