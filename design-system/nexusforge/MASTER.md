# NexusForge Design System - MASTER.md

## NexusForge - AI Developer Platform Design System

### 1. Pattern
- **Name**: Product Demo + Features
- **Conversion**: Use interactive demo only when explaining value better than static media. Provide captions, transcript, visible play/pause controls, and non-video fallback. Pause media when offscreen or hidden and keep final product state available as static content. Pause media when offscreen or hidden and keep final product state available as static content.
- **CTA**: Video center + CTA right/bottom
- **Sections**:
  1. Hero
  2. Product video/mockup (center)
  3. Feature breakdown per section
  4. Comparison (optional)
  5. CTA

### 2. Style
- **Name**: AI-Native UI
- **Mode Support**: Light supported, Dark supported
- **Keywords**: Chatbot, conversational, voice, assistant, agentic, ambient, minimal, chrome, streaming text, AI interactions
- **Best For**: AI products, chatbots, voice assistants, copilots, AI-powered tools, conversational interfaces
- **Performance**: cost:low|drivers:none
- **Accessibility**: risk:low|requires:contrast-text-4.5,keyboard,visible-focus,reduced-motion

### 3. Colors
- **Primary**: #7C3AED (--color-primary)
- **On Primary**: #FFFFFF (--color-on-primary)
- **Secondary**: #A78BFA (--color-secondary)
- **On Secondary**: #0F172A (--color-on-secondary)
- **Accent/CTA**: #0891B2 (--color-accent)
- **On Accent/CTA**: #000000 (--color-on-accent)
- **Background**: #FAF5FF (--color-background)
- **Foreground**: #1E1B4B (--color-foreground)
- **Card**: #FFFFFF (--color-card)
- **Card Foreground**: #1E1B4B (--color-card-foreground)
- **Muted**: #ECEEF9 (--color-muted)
- **Muted Foreground**: #475569 (--color-muted-foreground)
- **Border**: #DDD6FE (--color-border)
- **Destructive**: #DC2626 (--color-destructive)
- **On Destructive**: #FFFFFF (--color-on-destructive)
- **Ring**: #7C3AED (--color-ring)
- **Notes**: AI purple + cyan interactions [Accent adjusted from #06B6D4]

### 4. Typography
- **Font**: Inter
- **Mood**: dark, cinematic, technical, precision, clean, premium, developer, professional, high-end utility
- **Google Fonts**: https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap
- **CSS Import**: @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap')

### 5. Key Effects
- Typing indicators (3-dot pulse)
- Streaming text animations
- Pulse animations
- Context cards
- Smooth reveals

### 6. AVOID
- Heavy chrome + Slow response feedback

### 7. Pre-Delivery Checklist
- [ ] No emojis as icons (use SVG: Heroicons/Lucide)
- [ ] cursor-pointer on all clickable elements
- [ ] Hover states with smooth transitions (150-300ms)
- [ ] Light mode: text contrast 4.5:1 minimum
- [ ] Focus states visible for keyboard nav
- [ ] prefers-reduced-motion respected
- [ ] Responsive: 375px, 768px, 1024px, 1440px

### 8. Component Guidelines
#### Card
- Use card pattern for content sections
- Card: #FFFFFF (--color-card)
- Card Foreground: #1E1B4B (--color-card-foreground)
- Card Border: #DDD6FE (--color-border)
- Card Padding: 24px

#### Button
- Primary: #0891B2 (--color-accent)
- Primary Text: #FFFFFF (--color-on-accent)
- Secondary: #A78BFA (--color-secondary)
- Secondary Text: #0F172A (--color-on-secondary)
- Muted: #ECEEF9 (--color-muted)
- Muted Text: #475569 (--color-muted-foreground)

#### Input Field
- Border: #DDD6FE (--color-border)
- Focus Border: #7C3AED (--color-primary)
- Background: #FAF5FF (--color-background)
- Text: #1E1B4B (--color-foreground)
- Error: #DC2626 (--color-destructive)
- Error Text: #DC2626 (--color-destructive)

#### Modal
- Background: #1E1B4B + 80% opacity
- Content: #FFFFFF (--color-card)
- Close Button: #DC2626 (--color-destructive)
- Close Icon: #FFFFFF (--color-on-destructive)

### 9. Responsive Design
- Mobile: 375px (default)
- Tablet: 768px
- Desktop: 1024px
- Large Desktop: 1440px
- Breakpoints: 375px, 768px, 1024px, 1440px
- Mobile-first approach

### 10. Accessibility
- Contrast ratio 4.5:1 minimum for text
- Keyboard navigation fully supported
- Screen reader support for all interactive elements
- Reduced motion support respected
- Focus indicators visible and 3:1 contrast
- Skip to main content links
- Form labels always visible (not placeholder-only)

### 11. Design Dials (Optional)
- --variance: 1-10 (1=Minimalist, 10=Bold/Asymmetric)
- --motion: 1-10 (1=Subtle, 10=Complex)
- --density: 1-10 (1=Spacious, 10=Dense)

### 12. Style Tokens
- --color-primary: #7C3AED
- --color-on-primary: #FFFFFF
- --color-secondary: #A78BFA
- --color-on-secondary: #0F172A
- --color-accent: #0891B2
- --color-on-accent: #000000
- --color-background: #FAF5FF
- --color-foreground: #1E1B4B
- --color-card: #FFFFFF
- --color-card-foreground: #1E1B4B
- --color-muted: #ECEEF9
- --color-muted-foreground: #475569
- --color-border: #DDD6FE
- --color-destructive: #DC2626
- --color-on-destructive: #FFFFFF
- --color-ring: #7C3AED

### 12. Frontend Crash State
- Background: `#0f172a` (`#1E1B4B` + dark) — same dark token as design
- Error text: `#f87171` (red) — visible on dark
- Font: Inter / monospace — match design
- Preformatted white-space (`pre-wrap`) — stack traces readable
- Must print `error.name`, `error.message`, `error.stack` (Safari/iOS `msg` is generic)
- See: `references/frontend-deploy-debug.md`