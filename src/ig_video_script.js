(() => {
  let mp4Links = new Set();
  let observer;
  let scrolling = true;
  let counter = 0;

  function collectVideoLinks() {
    /** 
  
     UPDATED SCRAPER FOR THE NEWER INSTAGRAM UPDATE
  
  **/
    document.querySelectorAll('video').forEach(v => {
      const src = v.currentSrc || v.src;
     
      if (src && src.includes('.mp4') && !src.startsWith('blob:')) {
        if (!mp4Links.has(src)) {
          mp4Links.add(src);
          console.log(`🎥 [TAG] Found #${++counter}:`, src.split('?')[0]);
        }
      }
    });

    document.querySelectorAll('[data-video-url]').forEach(container => {
      const src = container.getAttribute('data-video-url');
      if (src && src.includes('.mp4') && !mp4Links.has(src)) {
        mp4Links.add(src);
        console.log(`🎥 [DATA] Found #${++counter}:`, src.split('?')[0]);
      }
    });
  }

  observer = new MutationObserver(() => collectVideoLinks());
  observer.observe(document.body, { childList: true, subtree: true });

  collectVideoLinks();

  const SCROLL_DELAY = 3000; 
  const SCROLL_STEP = window.innerHeight * 0.8;

  function scrollOnce() {
    if (!scrolling) return;
    window.scrollBy(0, SCROLL_STEP);
    setTimeout(scrollOnce, SCROLL_DELAY);
  }
  scrollOnce();

  window.stop = function() {
    scrolling = false;
    if (observer) observer.disconnect();

    const text = Array.from(mp4Links).join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'social_media_videos.txt';
    a.click();
    URL.revokeObjectURL(a.href);

    console.log(`%c✅ Saved ${mp4Links.size} permanent links!`, 'color: lime; font-weight: bold;');
  };

  console.log('%c[Universal Video Tracker Active]', 'color: cyan; font-weight: bold;');
  console.log('Tracking both <video> tags and [data-video-url] containers.');
  console.log('Type stop() to finish and download.');
})();
