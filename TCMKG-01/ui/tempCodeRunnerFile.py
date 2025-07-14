    """更新所有界面文本"""
        # 更新窗口标题
        self.update_window_title()
        
        # 更新工具栏按钮文本
        self.file_btn.setText(self.lang_manager.get_text("file_menu"))
        self.edit_btn.setText(self.lang_manager.get_text("edit_menu"))
        self.view_btn.setText(self.lang_manager.get_text("view_menu"))
        self.language_btn.setText(self.lang_manager.get_text("language"))
        self.plugin_btn.setText(self.lang_manager.get_text("plugin_menu"))
        
        # 更新菜单项
        self.update_menu_texts()
        
        # 更新模式相关文本
        self.mode_label.setText(self.lang_manager.get_text("display_mode"))
        self.refresh_view_btn.setText(self.lang_manager.get_text("refresh_view"))
        
        # 【修复】：更新控制栏中的显示模式标签
        if hasattr(self, 'display_mode_label'):
            self.display_mode_label.setText(self.lang_manager.get_text("display_mode"))
        
        # 更新快速模式按钮
        self.update_quick_mode_button()
        
        # 更新状态和其他动态文本
        self.update_toolbar_stats()
        
        # 【重要添加】：更新节点详情面板的文本
        self.node_detail.update_ui_texts()
        
        # 如果当前在数据模式，重新渲染以应用新语言
        if hasattr(self, 'current_mode') and self.current_mode == "data":
            self.render_data_mode()
        
        # 更新模式状态标签
        if hasattr(self, 'mode_status_label'):
            if hasattr(self, 'current_mode'):
                if self.current_mode == "graph":
                    self.mode_status_label.setText(self.lang_manager.get_text("current_graph_mode"))
                else:
                    self.mode_status_label.setText(self.lang_manager.get_text("current_data_mode"))

        # 更新其他界面元素
        if hasattr(self, 'mode_switch_btn'):
            if hasattr(self, 'current_mode'):
                if self.current_mode == "graph":
                    self.mode_switch_btn.setText(self.lang_manager.get_text("switch_to_data"))
                else:
                    self.mode_switch_btn.setText(self.lang_manager.get_text("switch_to_graph"))

        if hasattr(self, 'refresh_btn'):
            self.refresh_btn.setText(self.lang_manager.get_text("refresh_view"))

        if hasattr(self, 'data_mode_title'):
            self.data_mode_title.setText(self.lang_manager.get_text("data_detail_mode"))

        if hasattr(self, 'export_view_btn'):
            self.export_view_btn.setText(self.lang_manager.get_text("export_current_view"))

        if hasattr(self, 'graph_status'):
            self.update_graph_status(self.lang_manager.get_text("graph_loading"))