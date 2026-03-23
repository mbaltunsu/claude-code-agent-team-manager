# Frontend Rules

## Design & Skills

- Always prioritize using skills or agents in the project that are specialized in frontend or UI/UX design if they exist
- Before building any UI component, check if a design skill or agent is available and use it

## Text & Content

- Do not make static texts selectable (`user-select: none` on labels, headings, buttons)
- Always truncate long text with ellipsis instead of breaking layouts
- Use placeholder/skeleton screens instead of blank empty states

## Loading & Feedback

- Always manage loading state of buttons and pages by adding a loading spinner
- Disable buttons while their action is in progress to prevent double submission
- Show skeleton loaders for content that takes time to fetch

## Notifications

- Always use toast notifications for any action that changes important state, saves data, or produces an error
- Success actions: brief toast (auto-dismiss)
- Errors: persistent toast with clear message until dismissed by user
- Never fail silently — every user action must have visible feedback

## Forms & Inputs

- Validate inputs on blur, not only on submit
- Show inline error messages next to the invalid field
- Preserve user input on validation failure — never clear the form

## Accessibility

- Every interactive element must be keyboard accessible
- Images must have alt text
- Maintain sufficient color contrast (WCAG AA minimum)
- Focus states must be visible on all interactive elements

## Responsiveness

- Mobile-first approach — design for small screens, then scale up
- Touch targets must be at least 44x44px on mobile
- Test layouts at 320px, 768px, and 1280px breakpoints minimum

## Performance

- Lazy load images and heavy components below the fold
- Avoid layout shift — always set explicit dimensions on images and media
- Defer non-critical scripts and styles

## SEO & SEA

- Add tags,files,functions required for SEO&SEA, use related agent if exists
