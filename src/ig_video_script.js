(() => {
  let mp4Links = new Set();
  let observer;
  let scrolling = true;

 
  function collectVideoLinks() {
    document.querySelectorAll('video').forEach(v => {
      const src = v.currentSrc || v.src;
      if (src && src.includes('.mp4') && !mp4Links.has(src)) {
        mp4Links.add(src);
        console.log('🎥 Found IG video:', src);
      }
    });
  }


  observer = new MutationObserver(() => collectVideoLinks());
  observer.observe(document.body, { childList: true, subtree: true });

  collectVideoLinks();

  const SCROLL_DELAY = 2500;       
  const SCROLL_STEP = window.innerHeight * 0.9;

  function scrollOnce() {
    if (!scrolling) return;
    window.scrollBy(0, SCROLL_STEP);
    setTimeout(scrollOnce, SCROLL_DELAY);
  }
  //scrollOnce();


  window.stop = function() {
    scrolling = false;       
    if (observer) observer.disconnect();

    const text = Array.from(mp4Links).join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'instagram_videos.txt';
    a.click();
    URL.revokeObjectURL(a.href);

    console.log(`✅ Saved ${mp4Links.size} video link(s) to instagram_videos.txt`);
    console.log('🛑 Tracking and auto-scroll stopped.');
  };

  console.log('▶ Instagram video tracker running.');
  console.log('Scroll through feed or Reels, new videos will be tracked automatically.');
  console.log('Call stop() to export all found video links.');
})();
