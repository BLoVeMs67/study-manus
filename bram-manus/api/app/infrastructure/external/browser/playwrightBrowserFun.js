// 获取当前网页可见内容的所有元素
const getVisibleContent = () => {
    // 1.定义变量存储所有可视元素+视口的宽高
    const visibleElements = [];
    const viewportHeight = window.innerHeight;
    const viewportWidth = window.innerWidth;

    // 2.获取页面上的所有元素（包含可见+不可见）
    const elements = document.querySelectorAll("body *");

    // 3.循环遍历所有dom逐个处理
    for (let i = 0; i < elements.length; i++){
        // 4.获取dom元素的尺寸+位置
        const element = elements[i]
        const rect = element.getBoundingClientRect()

        // 5.判断元素的宽高，只要有一个为0就是不可见
        if (rect.height === 0 || rect.width === 0) continue;

        // 6.排除完全不在当前视口内的元素（上下左右）
        if (
            rect.bottom < 0 ||
            rect.top > viewportHeight ||
            rect.right < 0 ||
            rect.left > viewportWidth
        ) continue;

        // 7.使用样式判断当前元素是否隐藏
        const style = window.getComputedStyle(element);
        if (
            style.display === 'none' || // 块隐藏
            style.visibility === 'hidden' || // 不可见
            style.opacity === '0' // 透明度
        ) continue;

        // 8.如果element为有意义的节点/元素，则添加进来
        if (
            element.innerText ||
            element.tagName === "IMG" ||
            element.tagName === "INPUT" ||
            element.tagName === "BUTTON"
        ) visibleElements.push(element.outerHTML)
    }

    // 9.将所有的可视元素组装成字符串并拼接到div标签中直接返回
    return "<div>" + visibleElements.join(" ") + "</div>>"
}