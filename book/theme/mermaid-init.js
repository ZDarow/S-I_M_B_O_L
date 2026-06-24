// Mermaid.js initializer for mdBook
(function() {
    // Wait for the page to load, then render mermaid diagrams
    const initMermaid = function() {
        if (typeof mermaid === 'undefined') {
            // Mermaid not loaded yet
            return;
        }
        mermaid.initialize({
            startOnLoad: true,
            theme: 'default',
            themeVariables: {
                fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
                fontSize: '14px',
                primaryColor: '#1565c0',
                primaryTextColor: '#fff',
                primaryBorderColor: '#0d47a1',
                lineColor: '#1565c0',
                secondaryColor: '#e3f2fd',
                tertiaryColor: '#f5f5f5'
            },
            flowchart: { useMaxWidth: true, htmlLabels: true },
            sequence: { useMaxWidth: true, showSequenceNumbers: true }
        });
        
        // Re-render mermaid blocks inside the content area
        const mermaidBlocks = document.querySelectorAll('.content pre code.language-mermaid');
        mermaidBlocks.forEach(function(block) {
            const pre = block.parentElement;
            const wrapper = document.createElement('div');
            wrapper.className = 'mermaid';
            wrapper.textContent = block.textContent;
            pre.parentNode.replaceChild(wrapper, pre);
        });
        
        if (mermaidBlocks.length > 0) {
            mermaid.run({ nodes: document.querySelectorAll('.mermaid') });
        }
    };

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initMermaid);
    } else {
        initMermaid();
    }
    
    // Re-run on navigation (mdBook uses SPA-like navigation)
    document.addEventListener('mdbook-content-changed', initMermaid);
})();
