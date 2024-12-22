 // JavaScript code goes here
    function showPanel(panelId) {
      var panels = document.querySelectorAll('.panel');
      var buttons = document.querySelectorAll('.toggle-buttons button');

      panels.forEach(function(panel) {
        panel.style.display = panel.id === panelId ? 'block' : 'none';
      });

      buttons.forEach(function(button) {
        if (button.id === panelId + 'Btn') {
          button.classList.add('active');
        } else {
          button.classList.remove('active');
        }
      });
    }
    // 显示/隐藏调试器
