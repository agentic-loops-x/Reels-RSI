// territory ring, counter-clockwise (wrong for d3-geo)
const TERRITORY = [[100, 40], [100, 25], [120, 25], [120, 40], [100, 40]];
const feature = { type: "Feature", geometry: { type: "Polygon", coordinates: [TERRITORY] } };
