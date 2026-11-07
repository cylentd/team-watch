
export const WAIVERS_MOTION = Object.freeze({
  weeks: 6,      // the storyboard's strip: Love's six starts (the view passes the edition's own count)
  glow: .5,      // s a card's rim light takes to fade after it lands
  overlap: 2,    // each week fills over two steps of the strip's span, so the fill reads as one sweep
});

// Preserved waivers-data.mjs configuration from the approved film cut.
export const WAIVERS_DATA_DETAIL = Object.freeze({
  through: 8,
  pickupCount: 3,
});

// Preserved waivers-view.mjs configuration from the approved film cut.
export const WAIVERS_VIEW_DETAIL = Object.freeze({
  viewportPercent: 100,
});
