"use client"

import {useParams, useRouter} from "next/navigation";
import {Sidebar, SidebarContent, SidebarHeader, SidebarTrigger} from "@/components/ui/sidebar";
import {MessageSquareText, MoreHorizontal, Plus, Trash} from "lucide-react";
import {Button} from "@/components/ui/button";
import {Kbd, KbdGroup} from "@/components/ui/kbd";
import {Item, ItemActions, ItemContent, ItemDescription, ItemGroup, ItemMedia, ItemTitle} from "@/components/ui/item";
import {Avatar, AvatarGroupCount} from "@/components/ui/avatar";
import {DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger} from "@/components/ui/dropdown-menu";

export function LeftPanel() {
  const router = useRouter()
  const params = useParams()
  const sessions = [
    "1", "2", "3"
  ]
  return (
      <Sidebar>
        {/* 顶部的切换按钮 */}
        <SidebarHeader>
          <SidebarTrigger className="cursor-pointer"/>
        </SidebarHeader>
        <SidebarContent className="p-2">
          {/* 新建任务 */}
          <Button
              variant="outline"
              className="cursor-pointer mb-3"
              onClick={() => router.push('/')}
          >
            <Plus/>
            新建任务
            <KbdGroup>
              <Kbd>⌘</Kbd>
              <Kbd>K</Kbd>
            </KbdGroup>
          </Button>
          {/* 会话列表 */}
          <ItemGroup className="gap-1">
            {sessions.map((session) => (
                <Item
                    key="session"
                    className={`p-2 hover:bg-white cursor-pointer gap-2 ${session === params?.id ? "bg-white" : ""}`}
                    onClick={() => router.push(`/sessions/${session}`)}
                >
                  {/* 左侧图标 */}
                  <ItemMedia>
                    <Avatar className={"size-8"}>
                      <AvatarGroupCount>
                        <MessageSquareText/>
                      </AvatarGroupCount>
                    </Avatar>
                  </ItemMedia>
                  {/* 中间内容 */}
                  <ItemContent className={"gap-0"}>
                    <ItemTitle className={"text-md font-medium line-clamp-1"}>
                      图片合并为PDF的操作计划
                    </ItemTitle>
                    <ItemDescription
                        className={"text-xs line-clamp-1"}
                    >
                      您上传的4张图片已成功合并为一个PDF文件
                    </ItemDescription>
                  </ItemContent>
                  {/* 右侧操作区 */}
                  <ItemActions className="flex flex-col pt-1 gap-0">
                    {/*<div className={"flex flex-col pt-1"}>*/}
                    <ItemDescription className={"text-xs"}>周一</ItemDescription>
                    <DropdownMenu>
                      {/*<DropdownMenuTrigger asChild>*/}
                      <DropdownMenuTrigger>
                        <Button size="icon-xs" variant="ghost" className={"cursor-pointer"}>
                          <MoreHorizontal/>
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align={"center"} side={"bottom"}>
                        <DropdownMenuItem variant={"destructive"} className={"cursor-pointer"}>
                          <Trash/>
                          删除
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                    {/*</div>*/}
                  </ItemActions>
                </Item>
            ))}
          </ItemGroup>
        </SidebarContent>
      </Sidebar>
  )
}
