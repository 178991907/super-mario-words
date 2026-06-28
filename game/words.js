/**
 * ============================================================================
 * 🍄 马里奥英语单词冒险游乐场 (Super Mario Words) - 核心词汇控制引擎
 * ============================================================================
 * 💡 项目声明与致谢 (Project Credits):
 * 
 *   - 本项目由 Kenneth 提出项目创意、策划游戏玩法并主导实现核心游戏功能。
 *   - 由 AI 智能编码助手 (Antigravity) 协作辅助研发编写代码并最终成功开发部署。
 * 
 * ============================================================================
 */
(function() {
  window.WordSystem = {
    words: [],
    learnedCount: 0,
    currentLevel: 1, // 1: 小学, 2: 初中
    history: [], // 本次游戏弹出的单词历史

    init: function() {
      // 强制在 LocalStorage 中重置静音状态为 false，确保第一次进游戏必定有原版声音和背景音乐
      localStorage.setItem('muted', 'false');
      
      var savedWords = localStorage.getItem('mario_words');
      if (savedWords) {
        try {
          this.words = JSON.parse(savedWords);
          this.initProgress();
        } catch(e) {
          this.loadDefaultWords();
        }
      } else {
        this.loadDefaultWords();
      }
    },

    loadDefaultWords: function() {
      var self = this;
      // 由于 game/mario.html 相比 data/words.json 处于 game 目录下，使用相对路径 ../data/words.json
      fetch('../data/words.json')
        .then(function(res) { return res.json(); })
        .then(function(data) {
          self.words = data.words || [];
          localStorage.setItem('mario_words', JSON.stringify(self.words));
          self.initProgress();
        })
        .catch(function(err) {
          console.error('加载默认词库失败，使用内置降级词库', err);
          self.words = [
            {"en": "apple", "cn": "苹果", "level": 1, "example": "A red apple."},
            {"en": "banana", "cn": "香蕉", "level": 1, "example": "Yellow banana."},
            {"en": "orange", "cn": "橙子", "level": 1, "example": "Sweet orange."},
            {"en": "water", "cn": "水", "level": 1, "example": "Drink water."},
            {"en": "school", "cn": "学校", "level": 1, "example": "Go to school."}
          ];
          self.initProgress();
        });
    },

    initProgress: function() {
      this.learnedCount = parseInt(localStorage.getItem('mario_learned_count') || '0', 10);
      this.currentLevel = parseInt(localStorage.getItem('mario_level') || '1', 10);
    },

    getRandomWord: function() {
      if (!this.words || this.words.length === 0) {
        return { en: "mario", cn: "马里奥", example: "Super Mario!" };
      }
      var self = this;
      // 筛选出符合当前 Level 的单词
      var filtered = this.words.filter(function(w) {
        return parseInt(w.level, 10) === self.currentLevel;
      });
      if (filtered.length === 0) {
        filtered = this.words;
      }
      var randomIndex = Math.floor(Math.random() * filtered.length);
      var word = filtered[randomIndex];

      // 增加已学单词数
      this.learnedCount++;
      localStorage.setItem('mario_learned_count', this.learnedCount);
      
      // 记录历史
      this.history.push(word);
      if (this.history.length > 50) {
        this.history.shift();
      }

      return word;
    },

    setLevel: function(level) {
      this.currentLevel = parseInt(level, 10);
      localStorage.setItem('mario_level', this.currentLevel);
    },

    // 提供给管理后台使用的 API
    updateWordsList: function(newWords) {
      this.words = newWords;
      localStorage.setItem('mario_words', JSON.stringify(newWords));
    }
  };

  window.WordSystem.init();
})();
