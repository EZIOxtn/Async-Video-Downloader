(() => {
  let mp4Links = new Set();
  let observer;
  let counterVideo = 0;


  /** 
  
     UPDATED SCRAPER FOR THE NEWER FACEBOOK UPDATE
  
  **/
  function collectVideoLinks() {
 
    document.querySelectorAll('[data-video-url]').forEach(container => {
      const src = container.getAttribute('data-video-url');
      
      if (src && src.includes('.mp4')) {
        if (!mp4Links.has(src)) {
          mp4Links.add(src);
          console.log(`🎥 Found #${counterVideo++}:`, src.substring(0, 100) + '...');
        }
      }
    });
  }

  observer = new MutationObserver(() => collectVideoLinks());
  observer.observe(document.body, { childList: true, subtree: true });

  collectVideoLinks();

  console.log('%c[Facebook Video Tracker Started]', 'color: lime; font-weight: bold;');
  console.log('Scanning for data-video-url attributes...');

  // Export Logic
  window.stop = function() {
    if (observer) observer.disconnect();
    console.log('%c[Tracking stopped]', 'color: red; font-weight: bold;');

    const text = Array.from(mp4Links).join('\n');
    const blob = new Blob([text], { type: 'text/plain' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'fb_video_links.txt';
    a.click();
    URL.revokeObjectURL(a.href);

    console.log(`✅ Saved ${mp4Links.size} permanent link(s) to fb_video_links.txt`);
  };


  let scrolling = true;
  const SCROLL_DELAY = 3000; 
  const SCROLL_STEP = window.innerHeight * 0.8;

  function scrollOnce() {
    if (!scrolling) return;
    window.scrollBy(0, SCROLL_STEP);
    setTimeout(scrollOnce, SCROLL_DELAY);
  }
  
  scrollOnce();

  window.stopAutoScroll = function() {
    scrolling = false;
    console.log('🛑 Auto-scroll stopped.');
  };
})();
