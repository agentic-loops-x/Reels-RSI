// territory ring, clockwise on the map (north edge eastward, then south, then west)
const TERRITORY = [[100, 40], [120, 40], [120, 25], [100, 25], [100, 40]];
const feature = { type: "Feature", geometry: { type: "Polygon", coordinates: [TERRITORY] } };
// a route is not a ring — never flagged
const route = [[116.4, 39.9], [118.8, 32.0], [121.5, 31.2], [113.3, 23.1]];
