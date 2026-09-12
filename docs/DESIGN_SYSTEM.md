# NexusForge Design System

## Brand Aesthetic
Precision-engineered, minimalist, high-contrast dark mode. Zero clutter, clean borders, 8px spacing grid.

## Color Palette Tokens
- **Base Canvas**: `#090A0F` (Obsidian background)
- **Surface / Cards**: `#12151E` (Raised panels, modals)
- **Elevated / Hover**: `#1A1F2C`
- **Brand Primary**: `#007BFF` (Electric Azure from logo)
- **Brand Neutral**: `#7D8597` (Titanium Gray from logo)
- **Border Subtle**: `#1E2433`
- **Text Primary**: `#F3F4F6`
- **Text Muted**: `#8E95A5`
- **Telemetry Success**: `#10B981`
- **Telemetry Error**: `#EF4444`
- **Telemetry Warning**: `#F59E0B`

## Typography
- Interface: Sans-serif (`Inter`, system-ui)
- Data/Logs: Monospace (`JetBrains Mono`, Menlo)

## Component Styling Guidelines

### Root Layout & Safe Area
- Background: `#090A0F`
- Mobile notch spacing: `padding-top: max(16px, env(safe-area-inset-top));`

### Cards & Containers
- Background: `#12151E`
- Border: `1px solid #1E2433`
- Border-radius: `10px`
- Padding: `16px`
- Margin-bottom: `16px`
- Box-shadow: `0 1px 3px rgba(0,0,0,0.05)`

### System Status Grid
- Layout: 3-column horizontal grid (`grid-template-columns: repeat(3, 1fr)`)
- Status indicators: 
  - Online: `background: rgba(16, 185, 129, 0.1); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.2);`
  - Error: `background: rgba(239, 68, 68, 0.1); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.2);`

### Metrics Display
- Large numeric counters: `font-size: 28px; font-weight: 700; color: #007BFF; font-family: monospace;`
- Subtle sub-labels with `color: #8E95A5`

## Implementation Requirements
1. All UI elements must use CSS variables for colors and spacing
2. Mobile-first responsive design with 8px grid system
3. No hardcoded values - all colors, spacing, and sizing must use design tokens
4. Dark mode must be consistent across all components
5. Accessible components with proper contrast ratios

## Implementation Steps
1. Update CSS variables in `src/index.css`
2. Refactor Dashboard layout with new card structure
3. Update System Status component to use 3-column grid with pill badges
4. Implement metric grid for Active Executions and Recent Events
5. Update all card components to match design system
6. Verify mobile layout with safe area padding
7. Commit changes and update documentation