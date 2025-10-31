(() => {
  let mp4Links = new Set();
  let observer;
  let contervide = 0;
  // Function to check all <video> tags and extract mp4 links
  function collectVideoLinks() {
    document.querySelectorAll('video').forEach(v => {
      const src = v.currentSrc || v.src;
      if (src && src.includes('.mp4')) {
        if (!mp4Links.has(src)) {
          mp4Links.add(src); 
          console.log('🎥 Found: ' + contervide++, src);
        }
      }
    });
  }

 
  observer = new MutationObserver(() => collectVideoLinks());
  observer.observe(document.body, { childList: true, subtree: true });

  collectVideoLinks();

  console.log('%c[Video Tracker Started]', 'color: lime; font-weight: bold;');
  console.log('Scroll through reels — mp4 links will appear here.');
  console.log('When done, type %cstop()', 'color: yellow; font-weight: bold;', 'to export them.');

  window.stop = function() {
    if (observer) observer.disconnect();
    console.log('%c[Tracking stopped]', 'color: red; font-weight: bold;');

    const text = Array.from(mp4Links).join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'video_links.txt';
    a.click();
    URL.revokeObjectURL(a.href);

    console.log(`✅ Saved ${mp4Links.size} video link(s) to video_links.txt`);
  };

  // ---------------- Auto-scroll integration ----------------
  let scrolling = true;
  const SCROLL_DELAY = 3000; 
  const SCROLL_STEP = window.innerHeight * 0.9;

  function scrollOnce() {
    if (!scrolling) return;
    window.scrollBy(0, SCROLL_STEP);
    setTimeout(scrollOnce, SCROLL_DELAY);
  }

 
 

  
  window.stopAutoScroll = function() {
    scrolling = false;
    console.log('🛑 Auto-scroll stopped.');
  };

  console.log('▶ Auto-scroll started! Call stopAutoScroll() to stop.');
})();
