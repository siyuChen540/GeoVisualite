"""
    @author: Siyu Chen
    @email: chensy57@mail2.sysu.edu.cn
    @version: 3.6 (Integrated Toolbar Navigation & Bug Fix)
    @date: 2025/06/23
    @license: MIT License
    @description: An advanced geospatial data viewer for NetCDF and Shapefiles with a modern UI,
                 using PyQt5, Matplotlib, Geopandas, and Cartopy. Features integrated navigation
                 controls in the Matplotlib toolbar.
    @requirements: PyQt5, netCDF4, matplotlib, geopandas, cartopy, numpy, qtawesome
    @envinfo: pyqt_env
"""

import sys
import os
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


import netCDF4
import numpy as np
import geopandas as gpd

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar

import cartopy.crs as ccrs
from cartopy.mpl.geoaxes import GeoAxes

import qtawesome as qta

from PyQt5.QtWidgets import (QApplication, QMainWindow, QTextEdit, QPushButton, QVBoxLayout,
                             QWidget, QFileDialog, QHBoxLayout, QSplitter, QListWidget,
                             QTabWidget, QMessageBox, QListWidgetItem, QLabel, QDialog,
                             QFormLayout, QDialogButtonBox, QComboBox, QAction, QWidgetAction)
from PyQt5.QtGui import QTextCursor, QTextCharFormat, QColor, QFont
from PyQt5.QtCore import Qt, QSize


# --- Matplotlib and Cartopy Global Configuration ---
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# --- Modern UI Stylesheet (QSS) ---
def load_stylesheet(filename="style.qss"):
    try:
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        abs_path = os.path.join(base_path, filename)
        with open(abs_path, "r", encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Warning: Stylesheet '{filename}' not found. Using default styles.")
        return ""

class DimensionSelectorDialog(QDialog):
    # This class is unchanged from V3.5
    def __init__(self, var, parent=None):
        super().__init__(parent)
        self.setWindowTitle("选择维度、坐标轴和导航轴")
        self.var = var
        self.dimensions = var.dimensions
        self.shape = var.shape

        layout = QFormLayout(self)
        self.index_selectors = {}
        for dim, size in zip(self.dimensions, self.shape):
            combo = QComboBox()
            if size > 1000:
                 combo.addItems([str(i) for i in range(10)] + [f"... ({size-1})"])
            else:
                 combo.addItems([str(i) for i in range(size)])
            self.index_selectors[dim] = combo
            layout.addRow(f"{dim} 索引 (大小: {size})", combo)

        self.x_axis_combo = QComboBox()
        self.y_axis_combo = QComboBox()
        self.nav_axis_combo = QComboBox()

        self.x_axis_combo.addItems(self.dimensions)
        self.y_axis_combo.addItems(self.dimensions)
        
        lon_dims = [d for d in self.dimensions if 'lon' in d.lower()]
        lat_dims = [d for d in self.dimensions if 'lat' in d.lower()]
        if lon_dims: self.x_axis_combo.setCurrentText(lon_dims[0])
        if lat_dims: self.y_axis_combo.setCurrentText(lat_dims[0])
        
        self.update_nav_combo()

        self.x_axis_combo.currentTextChanged.connect(self.update_nav_combo)
        self.y_axis_combo.currentTextChanged.connect(self.update_nav_combo)

        layout.addRow("X 轴 (经度)", self.x_axis_combo)
        layout.addRow("Y 轴 (纬度)", self.y_axis_combo)
        layout.addRow("导航/步进维度", self.nav_axis_combo)

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def update_nav_combo(self):
        self.nav_axis_combo.clear()
        x_dim = self.x_axis_combo.currentText()
        y_dim = self.y_axis_combo.currentText()
        nav_dims = [dim for dim in self.dimensions if dim not in [x_dim, y_dim]]
        self.nav_axis_combo.addItems(["无"] + nav_dims)

    def get_selected_info(self):
        index_map = {dim: int(self.index_selectors[dim].currentText().split(' ')[0]) for dim in self.dimensions}
        x_dim = self.x_axis_combo.currentText()
        y_dim = self.y_axis_combo.currentText()
        nav_dim = self.nav_axis_combo.currentText()
        if nav_dim == "无":
            nav_dim = None

        if x_dim == y_dim:
            return None 
        
        return index_map, x_dim, y_dim, nav_dim

# MODIFICATION 1: Create a new toolbar class to integrate navigation controls
class NavigableCartopyToolbar(NavigationToolbar):
    def __init__(self, canvas, parent=None):
        super().__init__(canvas, parent)
        
        # Create navigation actions
        self.action_prev = QAction(qta.icon('fa5s.chevron-circle-left', color='#0078d7'), "上一个", self)
        self.action_next = QAction(qta.icon('fa5s.chevron-circle-right', color='#0078d7'), "下一个", self)
        
        # Create a label to show navigation info and wrap it in a QWidgetAction
        self.nav_label = QLabel("N/A")
        self.nav_label.setStyleSheet("padding: 0 10px;") # Add some spacing
        self.label_action = QWidgetAction(self)
        self.label_action.setDefaultWidget(self.nav_label)

        # Add actions to the toolbar
        self.addSeparator()
        self.addAction(self.action_prev)
        self.addAction(self.label_action)
        self.addAction(self.action_next)

        self.show_nav_controls(False) # Hide them by default

    def show_nav_controls(self, visible):
        self.action_prev.setVisible(visible)
        self.action_next.setVisible(visible)
        self.label_action.setVisible(visible)
    
    def update_nav_label(self, text):
        self.nav_label.setText(text)

    # --- Override methods for safety with Cartopy GeoAxes ---
    def home(self, *args):
        try:
            super().home(*args)
        except AttributeError:
            for ax in self.canvas.figure.axes:
                if isinstance(ax, GeoAxes):
                    ax.set_global()
                    ax._autoscaleXon = False
                    ax._autoscaleYon = False
            self.canvas.draw_idle()

    def back(self, *args):
        try: super().back(*args)
        except AttributeError: pass

    def forward(self, *args):
        try: super().forward(*args)
        except AttributeError: pass


class GeospatialTool(QMainWindow):
    def __init__(self):
        super().__init__()
        self.nc_dataset = None
        self.history_file = "history.txt"
        self.history = self.loadHistory()
        self.current_plot_info = {}
        self.initUI()
        self.return_to_initial_state()

    def initUI(self):
        self.setWindowTitle('地理空间数据可视化工具 (NC/SHP) - V3.6')
        self.setGeometry(100, 100, 1400, 900)
        self.setWindowIcon(qta.icon('fa5s.globe-asia', color="#acc3eb"))

        main_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Horizontal)

        # --- Left Panel ---
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 10, 10, 10)
        left_layout.setSpacing(10)

        self.btn_open_file = QPushButton(qta.icon('fa5s.folder-open', color='white'), ' 打开文件')
        self.btn_open_file.clicked.connect(self.show_file_dialog)
        self.btn_open_file.setIconSize(QSize(16, 16))

        self.btn_show_history = QPushButton(qta.icon('fa5s.history', color='white'), ' 显示历史')
        self.btn_show_history.clicked.connect(self.display_history)
        self.btn_show_history.setIconSize(QSize(16, 16))
        
        self.btn_return_home = QPushButton(qta.icon('fa5s.arrow-left', color='white'), ' 返回主界面')
        self.btn_return_home.clicked.connect(self.return_to_initial_state)
        self.btn_return_home.setIconSize(QSize(16, 16))

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.btn_open_file)
        button_layout.addWidget(self.btn_show_history)
        button_layout.addWidget(self.btn_return_home)

        variable_label = QLabel("可绘制变量 (双击绘图)")
        variable_label.setStyleSheet("font-weight: bold; padding: 5px 0;")
        self.variable_list = QListWidget(self)
        self.variable_list.itemDoubleClicked.connect(self.on_variable_selected)

        left_layout.addLayout(button_layout)
        left_layout.addWidget(variable_label)
        left_layout.addWidget(self.variable_list)

        # --- Main Area (Tabs) ---
        self.tabs = QTabWidget()
        self.info_tab = QWidget()
        self.plot_tab = QWidget()
        self.tabs.addTab(self.info_tab, "文件元数据")
        self.tabs.addTab(self.plot_tab, "数据可视化")

        info_layout = QVBoxLayout(self.info_tab)
        self.text_edit = QTextEdit(self)
        self.text_edit.setReadOnly(True)
        info_layout.addWidget(self.text_edit)

        # Plot Tab
        plot_layout = QVBoxLayout(self.plot_tab)
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)
        
        # MODIFICATION 1: Use the new NavigableCartopyToolbar
        self.toolbar = NavigableCartopyToolbar(self.canvas, self)
        self.toolbar.setObjectName("matplotlib-toolbar")
        # Connect the toolbar's navigation actions to the main window's methods
        self.toolbar.action_prev.triggered.connect(self.navigate_dim_prev)
        self.toolbar.action_next.triggered.connect(self.navigate_dim_next)
        
        plot_layout.addWidget(self.toolbar)
        plot_layout.addWidget(self.canvas)
        
        # Assembly
        splitter.addWidget(left_panel)
        splitter.addWidget(self.tabs)
        splitter.setSizes([350, 1050])
        splitter.setStretchFactor(1, 1)

        main_layout.addWidget(splitter)
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.setAcceptDrops(True)
    
    # def set_custom_coord_format(self, ax: GeoAxes):
    #     """
    #     为给定的 GeoAxes 设置自定义的鼠标坐标显示格式。
    #     默认格式为度分秒，这里修改为十进制度数。
    #     """
    #     def formatter(x: float, y: float) -> str:
    #         # 将经纬度格式化为带有4位小数的浮点数
    #         return f"坐标值 ({x:.4f}, {y:.4f})"
        
    #     ax.format_coord = formatter
    def set_custom_coord_format(self, ax: GeoAxes, data_array, x_coords_1d, y_coords_1d):
        """
        define the custom coordinate format for the GeoAxes.

        Args:
            ax: The GeoAxes object.
            data_array (np.array): 2D numpy array of the plotted data.
            x_coords_1d (np.array): 1D numpy array for longitude.
            y_coords_1d (np.array): 1D numpy array for latitude.
        """
        # If the coordinates are not provided, use a fallback formatter
        if x_coords_1d is None or y_coords_1d is None or x_coords_1d.ndim != 1 or y_coords_1d.ndim != 1:
            def fallback_formatter(x, y):
                return f"经度: {x:.4f}, 纬度: {y:.4f}"
            ax.format_coord = fallback_formatter
            return

        def formatter(x, y):
            # find the closest indices in the 1D coordinate arrays
            col_idx = np.abs(x_coords_1d - x).argmin()
            row_idx = np.abs(y_coords_1d - y).argmin()

            # check if the indices are within bounds of the data array
            if 0 <= row_idx < data_array.shape[0] and 0 <= col_idx < data_array.shape[1]:
                value = data_array[row_idx, col_idx]
                
                # process the value to handle masked arrays
                if np.ma.is_masked(value):
                    value_str = "N/A (masked)"
                else:
                    value_str = f"{value:.4f}" 
                
                return f"经度: {x:.4f}, 纬度: {y:.4f}, 值: {value_str}"
            else:
                # 如果鼠标在绘图区域外，则不显示值
                return f"经度: {x:.4f}, 纬度: {y:.4f}, 值: N/A (out of bounds)"
        
        # 将 ax 的坐标格式化函数设置为我们上面定义的 formatter
        ax.format_coord = formatter
    
    def return_to_initial_state(self):
        self.text_edit.clear()
        self.variable_list.clear()
        self.clear_plot()
        
        self.append_formatted_text("欢迎使用地理空间数据可视化工具", title=True)
        self.append_formatted_text("请通过拖拽或“打开文件”按钮加载 .nc 或 .shp 文件。")
        
        self.btn_open_file.setVisible(True)
        self.btn_show_history.setVisible(True)
        self.btn_return_home.setVisible(False)
        self.tabs.setCurrentWidget(self.info_tab)

    def display_history(self):
        self.text_edit.clear()
        self.variable_list.clear()
        self.clear_plot()
        
        if self.history:
            self.append_formatted_text("历史记录:", title=True)
            for filepath in self.history:
                self.append_formatted_text(filepath)
        else:
            self.append_formatted_text("没有历史记录.", italic=True)
            
        self.btn_open_file.setVisible(False)
        self.btn_show_history.setVisible(False)
        self.btn_return_home.setVisible(True)
        self.tabs.setCurrentWidget(self.info_tab)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.load_file(files[0])

    def show_file_dialog(self):
        fname, _ = QFileDialog.getOpenFileName(self, '打开文件', '',
                                             "All Supported Files (*.nc *.shp);;NetCDF files (*.nc);;Shapefiles (*.shp)")
        if fname:
            self.load_file(fname)

    def load_file(self, filepath):
        self.return_to_initial_state()
        self.text_edit.clear()

        _, ext = os.path.splitext(filepath)
        if ext.lower() == '.nc':
            self.load_nc_file(filepath)
        elif ext.lower() == '.shp':
            self.load_shp_file(filepath)
        else:
            self.show_error_message(f"不支持的文件类型: {ext}")
            return

        if filepath not in self.history:
            self.history.append(filepath)
            self.saveHistory()

    def load_nc_file(self, filepath):
        try:
            if self.nc_dataset:
                self.nc_dataset.close()
            self.nc_dataset = netCDF4.Dataset(filepath, 'r')
            self.append_formatted_text(f"文件: {filepath}\n", title=True)
            self.display_nc_metadata()
            self.populate_variable_list()
            self.tabs.setCurrentWidget(self.info_tab)
        except Exception as e:
            self.show_error_message(f"读取NC文件失败 {filepath}: {e}")
            self.nc_dataset = None

    def load_shp_file(self, filepath):
        try:
            self.append_formatted_text(f"文件: {filepath}\n", title=True)
            gdf = gpd.read_file(filepath)
            self.append_formatted_text("Shapefile 信息:", header=True)
            self.append_formatted_text(f"  坐标参考系统 (CRS): {gdf.crs}")
            self.append_formatted_text(f"  要素数量: {len(gdf)}")
            self.append_formatted_text(f"  几何类型: {gdf.geom_type.unique()}")
            self.plot_shp_data(gdf)
            self.tabs.setCurrentWidget(self.plot_tab)
        except Exception as e:
            self.show_error_message(f"读取SHP文件失败 {filepath}: {e}")
            
    # ... (display_nc_metadata, populate_variable_list methods are unchanged)
    def display_nc_metadata(self):
        if not self.nc_dataset: return
        self.append_formatted_text("全局属性:", header=True)
        if not self.nc_dataset.ncattrs():
             self.append_formatted_text("  (无)", italic=True)
        for attr_name in self.nc_dataset.ncattrs():
            self.append_formatted_text(f"  {attr_name}: {getattr(self.nc_dataset, attr_name)}")
        self.append_formatted_text("\n维度信息:", header=True)
        for dim_name, dim in self.nc_dataset.dimensions.items():
            self.append_formatted_text(f"  {dim_name}: size = {len(dim)}")
        self.append_formatted_text("\n变量信息:", header=True)
        for var_name, var in self.nc_dataset.variables.items():
            self.append_formatted_text(f"  {var_name}: dims={var.dimensions}, shape={var.shape}, type={var.dtype}", bold=True)
            for attr_name in var.ncattrs():
                self.append_formatted_text(f"    {attr_name}: {getattr(var, attr_name)}")

    def populate_variable_list(self):
        self.variable_list.clear()
        if not self.nc_dataset: return
        for var_name, var in self.nc_dataset.variables.items():
            if len(var.shape) >= 2:
                item_text = f"{var_name} {var.shape}"
                list_item = QListWidgetItem(qta.icon('fa5s.ruler-combined', color='#0078d7'), item_text)
                self.variable_list.addItem(list_item)
                
    def on_variable_selected(self, item):
        if not self.nc_dataset: return
        
        variable_name = item.text().split(' ')[0]
        var = self.nc_dataset.variables[variable_name]
        
        if var.ndim > 2:
            dialog = DimensionSelectorDialog(var, self)
            if dialog.exec_() == QDialog.Accepted:
                selected_info = dialog.get_selected_info()
                if selected_info is None:
                    self.show_error_message("X 和 Y 轴不能选择相同的维度。")
                    return
                index_map, x_dim, y_dim, nav_dim = selected_info
                self.setup_high_dim_plot(var, index_map, x_dim, y_dim, nav_dim)
        else:
            self.plot_nc_variable(variable_name)

    # --- Plotting methods ---
    
    def clear_plot(self):
        """Clears the figure and hides any plot-specific controls."""
        self.current_plot_info = {}
        self.toolbar.show_nav_controls(False) # MODIFICATION 1: Hide controls in toolbar
        self.figure.clear()
        self.canvas.draw()
        
    def setup_high_dim_plot(self, var, index_map, x_dim, y_dim, nav_dim):
        """Stores plotting info and triggers the first plot."""
        self.clear_plot()
        self.current_plot_info = {
            'var': var, 'index_map': index_map, 'x_dim': x_dim,
            'y_dim': y_dim, 'nav_dim': nav_dim
        }
        if nav_dim:
            self.toolbar.show_nav_controls(True) # MODIFICATION 1: Show controls in toolbar
        self.update_high_dim_plot()

    def update_high_dim_plot(self):
        """Plots the data based on current_plot_info. This is the core refresh function."""
        if not self.current_plot_info: return

        info = self.current_plot_info
        var, index_map, x_dim, y_dim, nav_dim = info.values()
        
        try:
            slice_obj = []
            for dim_name in var.dimensions:
                if dim_name in [x_dim, y_dim]:
                    slice_obj.append(slice(None))
                else:
                    slice_obj.append(index_map[dim_name])
            
            data = var[tuple(slice_obj)]
            x_vals = self.nc_dataset.variables.get(x_dim)
            y_vals = self.nc_dataset.variables.get(y_dim)

            if x_vals is None or y_vals is None:
                self.show_error_message("无法获取指定的经纬度坐标变量。")
                return
            
            x, y = x_vals[:], y_vals[:]
            
            # ANALYSIS 2 FIX: Robustly handle data/coordinate alignment
            if data.shape == (len(y), len(x)):
                # Data shape is (lat, lon), which is standard
                lon, lat = np.meshgrid(x, y)
            elif data.shape == (len(x), len(y)):
                # Data shape is (lon, lat), requires transpose for plotting
                lon, lat = np.meshgrid(x, y)
                data = data.T
            else:
                self.show_error_message(f"数据形状 {data.shape} 与坐标轴长度 (Y={len(y)}, X={len(x)}) 不匹配。")
                return

            self.figure.clear()
            ax = self.figure.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
            self.set_custom_coord_format(ax, data, x, y)  # Set custom coordinate format
            ax._autoscaleXon = False
            ax._autoscaleYon = False
            
            # The set_extent call should now be safe
            ax.set_extent([np.min(lon), np.max(lon), np.min(lat), np.max(lat)], crs=ccrs.PlateCarree())
            
            im = ax.pcolormesh(lon, lat, data, transform=ccrs.PlateCarree(), cmap='viridis', shading='auto')
            ax.coastlines()
            ax.gridlines(draw_labels=True, linestyle='--', color='gray', alpha=0.5)
            cbar = plt.colorbar(im, ax=ax, orientation='vertical', pad=0.08, shrink=0.8)
            cbar.set_label(f"{var.name} ({getattr(var, 'units', '')})")
            
            # Update title and navigation label in the toolbar
            slice_info = ", ".join([f"{k}={v}" for k, v in index_map.items() if k not in [x_dim, y_dim, nav_dim]])
            ax.set_title(f"{var.name} ({slice_info})", pad=20)

            if nav_dim:
                current_idx = index_map[nav_dim]
                max_idx = var.shape[var.dimensions.index(nav_dim)]
                self.toolbar.update_nav_label(f"{nav_dim}: {current_idx + 1} / {max_idx}")
                self.toolbar.action_prev.setEnabled(current_idx > 0)
                self.toolbar.action_next.setEnabled(current_idx < max_idx - 1)

            self.canvas.draw()
            self.tabs.setCurrentWidget(self.plot_tab)
            
        except Exception as e:
            self.show_error_message(f"高维数据绘图失败: {e}")
            self.clear_plot()

    # ... (Other methods like plot_nc_variable, plot_shp_data, navigate_dim, etc., remain largely the same)
    def plot_nc_variable(self, var_name):
        self.clear_plot()
        try:
            var = self.nc_dataset.variables[var_name]
            data = np.squeeze(var[:])
            if data.ndim != 2:
                self.show_error_message(f"变量 '{var_name}' 无法简化为二维数组 (shape: {data.shape}).")
                return
            lon_1d, lat_1d = None, None
            possible_lon_names = ['lon', 'longitude', 'x']
            possible_lat_names = ['lat', 'latitude', 'y']
            var_dims = var.dimensions
            
            # 尝试从变量的维度中寻找坐标轴名称
            lon_dim_name = next((d for d in var_dims for n in possible_lon_names if n in d.lower()), None)
            lat_dim_name = next((d for d in var_dims for n in possible_lat_names if n in d.lower()), None)

            if lon_dim_name and lat_dim_name:
                # 确保维度存在于文件中
                if lon_dim_name in self.nc_dataset.variables and lat_dim_name in self.nc_dataset.variables:
                    lon_1d = self.nc_dataset.variables[lon_dim_name][:]
                    lat_1d = self.nc_dataset.variables[lat_dim_name][:]
            
            lon, lat = self.find_nc_coords(var)
            if lon is None or lat is None:
                self.show_error_message(f"无法自动找到 '{var_name}' 的经纬度坐标。")
                return

            ax: GeoAxes = self.figure.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())
            self.set_custom_coord_format(ax, data, lon_1d, lat_1d)  # Set custom coordinate format
            ax._autoscaleXon = False
            ax._autoscaleYon = False
            ax.set_global()
            
            im = ax.pcolormesh(lon, lat, data, transform=ccrs.PlateCarree(), cmap='viridis', shading='auto')
            ax.coastlines()
            ax.gridlines(draw_labels=True, linestyle='--', color='gray', alpha=0.5)
            cbar = plt.colorbar(im, ax=ax, orientation='vertical', pad=0.08, shrink=0.8)
            cbar.set_label(f"{var_name} ({getattr(var, 'units', '')})")
            ax.set_title(f"变量: {getattr(var, 'long_name', var_name)}", pad=20)
            
            self.canvas.draw()
            self.tabs.setCurrentWidget(self.plot_tab)
        except Exception as e:
            self.show_error_message(f"绘制变量 '{var_name}' 出错: {e}")
            self.clear_plot()
            
    def plot_shp_data(self, gdf):
        self.clear_plot()
        try:
            source_crs = gdf.crs
            cartopy_crs = None
            if source_crs:
                try:
                    epsg = source_crs.to_epsg()
                    if epsg: cartopy_crs = ccrs.epsg(epsg)
                except Exception:
                    if source_crs.is_geographic:
                        cartopy_crs = ccrs.PlateCarree()
                        self.append_formatted_text("  提示: 已自动识别为WGS84地理坐标系。", italic=True)
                    else:
                        self.show_error_message("无法自动转换投影坐标系。请使用标准EPSG代码的Shapefile。")
                        return
            if not cartopy_crs:
                self.show_error_message("Shapefile缺少有效的或可识别的坐标参考系统(CRS)，无法绘图。")
                return

            ax: GeoAxes = self.figure.add_subplot(1, 1, 1, projection=ccrs.Mercator())
            ax._autoscaleXon = False
            ax._autoscaleYon = False
            minx, miny, maxx, maxy = gdf.total_bounds
            ax.set_extent([minx, maxx, miny, maxy], crs=cartopy_crs)
            ax.coastlines()
            ax.gridlines(draw_labels=True, linestyle='--', color='gray', alpha=0.5)
            gdf.plot(ax=ax, edgecolor='#333333', facecolor='#0078d7', alpha=0.6, transform=cartopy_crs)
            ax.set_title("Shapefile 可视化", pad=20)
            
            self.canvas.draw()
        except Exception as e:
            self.show_error_message(f"绘制SHP文件出错: {e}")
            self.clear_plot()

    def navigate_dim_prev(self):
        nav_dim = self.current_plot_info.get('nav_dim')
        if nav_dim:
            self.current_plot_info['index_map'][nav_dim] -= 1
            self.update_high_dim_plot()

    def navigate_dim_next(self):
        nav_dim = self.current_plot_info.get('nav_dim')
        if nav_dim:
            self.current_plot_info['index_map'][nav_dim] += 1
            self.update_high_dim_plot()

    def find_nc_coords(self, var):
        lon, lat = None, None
        possible_lon_names = ['lon', 'longitude', 'x']
        possible_lat_names = ['lat', 'latitude', 'y']
        
        var_dims = var.dimensions
        lon_dim_name = next((d for d in var_dims for n in possible_lon_names if n in d.lower()), None)
        lat_dim_name = next((d for d in var_dims for n in possible_lat_names if n in d.lower()), None)

        if lon_dim_name and lat_dim_name:
            lon = self.nc_dataset.variables.get(lon_dim_name, [])[:]
            lat = self.nc_dataset.variables.get(lat_dim_name, [])[:]
        else:
            lon_var_name = next((v for v in self.nc_dataset.variables for n in possible_lon_names if n in v.lower()), None)
            lat_var_name = next((v for v in self.nc_dataset.variables for n in possible_lat_names if n in v.lower()), None)
            if lon_var_name and lat_var_name:
                lon = self.nc_dataset.variables.get(lon_var_name, [])[:]
                lat = self.nc_dataset.variables.get(lat_var_name, [])[:]
        
        if lon is not None and lat is not None and lon.ndim == 1 and lat.ndim == 1:
            lon, lat = np.meshgrid(lon, lat)
        return lon, lat

    def loadHistory(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, "r", encoding='utf-8') as file:
                    return [line.strip() for line in file if line.strip()]
            except Exception as e: print(f"Warning: Could not load history file. {e}")
        return []

    def saveHistory(self):
        try:
            with open(self.history_file, "w", encoding='utf-8') as file:
                file.write("\n".join(self.history))
        except Exception as e: print(f"Warning: Could not save history file. {e}")

    def closeEvent(self, event):
        if self.nc_dataset: self.nc_dataset.close()
        event.accept()

    def append_formatted_text(self, text, title=False, header=False, bold=False, italic=False):
        cursor = self.text_edit.textCursor()
        cursor.movePosition(QTextCursor.End)
        char_format = QTextCharFormat()
        font = QFont("Segoe UI", 10)
        char_format.setFont(font)
        if title:
            font.setBold(True); font.setPointSize(15); char_format.setFont(font)
            char_format.setForeground(QColor("#0078d7"))
        elif header:
            font.setBold(True); font.setPointSize(12); char_format.setFont(font)
            char_format.setForeground(QColor("#333333"))
        elif bold:
            font.setBold(True); char_format.setFont(font)
        elif italic:
            font.setItalic(True); char_format.setFont(font); char_format.setForeground(QColor("gray"))
        cursor.insertText(text + "\n", char_format)
        self.text_edit.ensureCursorVisible()

    def show_error_message(self, message):
        QMessageBox.critical(self, "错误", message)
        self.append_formatted_text(f"错误: {message}", italic=True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    stylesheet = load_stylesheet("style.qss")
    if stylesheet:
        app.setStyleSheet(stylesheet)
    else:
        print("Using default styles as no stylesheet was found.")
    ex = GeospatialTool()
    ex.show()
    sys.exit(app.exec_())