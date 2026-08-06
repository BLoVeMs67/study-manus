"use client"

import {ChatHeader} from "@/components/chat-header";

export default function Page() {
  return (
      <div className="h-full flex flex-col">
        {/* 顶部header */}
        <ChatHeader/>
        {/* 中间对话框 - 垂直居中，视觉上移一个导航栏高度 */}
        <div className="flex-1 flex items-center justify-center px-4 py-6 sm:py-8 -mt-12 sm:-mt-16">
          <div className="w-full max-w-full sm:max-w-[768px] sm:min-w-[390px] mx-auto">
            {/* 对话提示内容 */}
            <div className="text-[24px] sm:text-[32px] font-bold mb-4 sm:mb-6 text-center sm:text-left">
              <div className="text-gray-700">您好, 慕学员</div>
              <div className="text-gray-500">我能为您做什么?</div>
            </div>
            {/* 对话框 */}
            <ChatInput
                ref={chatInputRef}
                className="mb-4 sm:mb-6"
                onSend={handleSend}
                disabled={sending}
            />
            {/* 推荐对话内容 */}
            <SuggestedQuestions onQuestionClick={handleQuestionClick}/>
          </div>
        </div>
      </div>
  )
}
