import type {Metadata} from "next";
import "./globals.css";
import {Geist} from "next/font/google";
import {cn} from "@/lib/utils";
import {SidebarProvider} from "@/components/ui/sidebar";
import {LeftPanel} from "@/components/left-panel";

const geist = Geist({subsets: ['latin'], variable: '--font-sans'});

export const metadata: Metadata = {
  title: "BramManus",
  description: "BramManus 是一个行动引擎，它超越了答案的范畴，可以执行任务、自动化工作流程，并扩展您的能力。",
  icons: {
    icon: "/icon.png"
  }
};

export default function RootLayout(
    {
      children
    }: LayoutProps<"/">) {
  return (
      <html lang="zh-CN" className={cn("font-sans", geist.variable)}>
      <body>
      <SidebarProvider
          style={{
            // eslint-disable-next-line @typescript-eslint/ban-ts-comment
            // @ts-expect-error
            '--sidebar-width': '300px',
            '--sidebar-width-icon': '300px',
          }}
      >
        {/* 左侧的面板 */}
        <LeftPanel/>
        {/* 右侧的内容 */}
        {children}
      </SidebarProvider>
      </body>
      </html>
  );
}
