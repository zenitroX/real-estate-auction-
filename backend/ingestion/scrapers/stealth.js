// Runs in every page before the site's own scripts. Hides the remaining
// differences between our server browser and a person's Chrome.
// Kept small on purpose: each patch here is something detectors actually check.
((languages) => {
  'use strict';

  // Patched functions must look native when inspected: toString() of each
  // replacement reports the original's source text ("function x() { [native code] }").
  const disguised = new WeakMap();
  const nativeToString = Function.prototype.toString;
  const toStringProxy = new Proxy(nativeToString, {
    apply: (target, thisArg, args) =>
      Reflect.apply(target, disguised.has(thisArg) ? disguised.get(thisArg) : thisArg, args),
  });
  disguised.set(toStringProxy, nativeToString);
  Function.prototype.toString = toStringProxy;

  const replace = (original, impl) => {
    const fake = new Proxy(original, { apply: (target, thisArg, args) => impl(target, thisArg, args) });
    disguised.set(fake, original);
    return fake;
  };

  // Servers have no GPU, so Chrome renders WebGL in software ("SwiftShader"),
  // a strong bot signal. Report a common laptop GPU that fits a Linux desktop.
  const VENDOR = 'Google Inc. (Intel)';
  const RENDERER = 'ANGLE (Intel, Mesa Intel(R) UHD Graphics 630 (CFL GT2), OpenGL 4.6)';
  for (const ctx of [self.WebGLRenderingContext, self.WebGL2RenderingContext]) {
    if (!ctx) continue;
    ctx.prototype.getParameter = replace(ctx.prototype.getParameter, (target, thisArg, args) => {
      if (args[0] === 0x9245) return VENDOR; // UNMASKED_VENDOR_WEBGL
      if (args[0] === 0x9246) return RENDERER; // UNMASKED_RENDERER_WEBGL
      return Reflect.apply(target, thisArg, args);
    });
  }

  // A person's Chrome lists the language and its base, e.g. ["en-US", "en"]
  const desc = Object.getOwnPropertyDescriptor(Navigator.prototype, 'languages');
  Object.defineProperty(Navigator.prototype, 'languages', {
    ...desc,
    get: replace(desc.get, () => languages.slice()),
  });
})(__LANGUAGES__);
