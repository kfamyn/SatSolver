import {continueRender, delayRender, staticFile} from 'remotion';

// Milky is the Scrollwall wordmark face (shipped in the app bundle).
const faces: [string, string, string][] = [
  ['Milky', 'Milky.ttf', '400'],
  ['Inter', 'Inter-SemiBold.otf', '600'],
  ['Inter', 'Inter-ExtraBold.otf', '800'],
  ['Inter', 'Inter-Black.otf', '900'],
];

const handle = delayRender('Loading fonts');
Promise.all(
  faces.map(([family, file, weight]) =>
    new FontFace(family, `url(${staticFile(`fonts/${file}`)})`, {weight})
      .load()
      .then((f) => (document.fonts as unknown as {add: (f: FontFace) => void}).add(f)),
  ),
)
  .then(() => continueRender(handle))
  .catch((e) => {
    console.error(e);
    continueRender(handle);
  });

export const UI = 'Inter, -apple-system, system-ui, sans-serif';
export const WORDMARK = 'Milky, Georgia, serif';
