import React from "react";

/* NexusForge Brand Logo - Geometric 'N' monogram
 * Left half: titanium gray (#7D8597) polygon
 * Right half: electric azure (#007BFF) polygon
 * Negative space forms the letter 'N'
 */
export const BrandLogo: React.FC<{ size?: number; className?: string }> = ({
  size = 32,
  className,
}) => {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 32 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-label="NexusForge Logo"
    >
      {/* Left half - Titanium Gray polygon */}
      <path d="M0 0H12.8L16 8L19.2 0H32V32H19.2L16 24L12.8 32H0V0Z" fill="#7D8597" />
      {/* Right half - Electric Azure polygon */}
      <path d="M12.8 0L16 8L19.2 0H32V32H19.2L16 24L12.8 32H0V0H12.8Z" fill="#007BFF" />
      {/* Negative space 'N' - created by the two overlapping triangles */}
    </svg>
  );
};

export default BrandLogo;