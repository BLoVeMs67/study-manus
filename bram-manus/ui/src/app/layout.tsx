import type {Metadata} from "next";
import "./globals.css";

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
        <html lang="zh-CN">
        <body>
        {children}
        </body>
        </html>
    );
}
