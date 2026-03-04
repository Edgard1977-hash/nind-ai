# 5. СИСТЕМА РАСШИРЯЕМОСТИ

## 5.1 Plugin Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       PLUGIN SYSTEM                                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    PLUGIN MANAGER                                │    │
│  │                                                                   │    │
│  │   ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │    │
│  │   │   Loader    │  │  Registry   │  │   Sandbox   │             │    │
│  │   │             │  │             │  │             │             │    │
│  │   │ - Validate  │  │ - Register  │  │ - Isolate   │             │    │
│  │   │ - Load      │  │ - Discover  │  │ - Monitor   │             │    │
│  │   │ - Init      │  │ - Version   │  │ - Limit     │             │    │
│  │   └─────────────┘  └─────────────┘  └─────────────┘             │    │
│  │                                                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    PLUGIN TYPES                                  │    │
│  │                                                                   │    │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │    │
│  │   │  ENGINE  │ │  MODEL   │ │ TEMPLATE │ │  EXPORT  │           │    │
│  │   │ PLUGINS  │ │ PLUGINS  │ │ PLUGINS  │ │ PLUGINS  │           │    │
│  │   └──────────┘ └──────────┘ └──────────┘ └──────────┘           │    │
│  │                                                                   │    │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │    │
│  │   │   UI     │ │ ANALYTICS│ │INTEGRATION│ │  STYLE   │           │    │
│  │   │ PLUGINS  │ │ PLUGINS  │ │  PLUGINS │ │ PLUGINS  │           │    │
│  │   └──────────┘ └──────────┘ └──────────┘ └──────────┘           │    │
│  │                                                                   │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## 5.2 Plugin Interface

```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BasePlugin(ABC):
    """
    Базовый интерфейс для всех плагинов
    """
    
    # Метаданные плагина
    PLUGIN_INFO = {
        "name": "",
        "version": "",
        "author": "",
        "description": "",
        "category": "",
        "requires": [],
        "provides": []
    }
    
    @abstractmethod
    async def initialize(self, config: Dict) -> bool:
        """Инициализация плагина"""
        pass
    
    @abstractmethod
    async def execute(self, input_data: Any) -> Any:
        """Основная логика плагина"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """Очистка ресурсов"""
        pass
    
    def get_capabilities(self) -> List[str]:
        """Список возможностей плагина"""
        return self.PLUGIN_INFO.get("provides", [])


class EnginePlugin(BasePlugin):
    """
    Плагин нового контент-движка
    """
    
    @abstractmethod
    async def process(self, task: Task) -> Result:
        """Обработка задачи"""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Поддерживаемые форматы"""
        pass


class ModelPlugin(BasePlugin):
    """
    Плагин новой AI-модели
    """
    
    @abstractmethod
    async def generate(self, prompt: str, params: Dict) -> Any:
        """Генерация контента"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict:
        """Информация о модели"""
        pass


class TemplatePlugin(BasePlugin):
    """
    Плагин шаблона
    """
    
    @abstractmethod
    def get_template_structure(self) -> Dict:
        """Структура шаблона"""
        pass
    
    @abstractmethod
    def get_variables(self) -> List[str]:
        """Переменные шаблона"""
        pass


class ExportPlugin(BasePlugin):
    """
    Плагин экспорта в новый формат
    """
    
    @abstractmethod
    async def export(self, content: Any, settings: Dict) -> bytes:
        """Экспорт контента"""
        pass
    
    @abstractmethod
    def get_export_formats(self) -> List[str]:
        """Форматы экспорта"""
        pass
```

## 5.3 Plugin Registry

```python
class PluginRegistry:
    """
    Реестр плагинов
    """
    
    def __init__(self):
        self._plugins: Dict[str, BasePlugin] = {}
        self._categories: Dict[str, List[str]] = {}
        self._dependencies: Dict[str, List[str]] = {}
    
    async def register(self, plugin: BasePlugin) -> bool:
        """
        Регистрация плагина
        """
        
        # Валидация
        if not self._validate_plugin(plugin):
            raise PluginValidationError(f"Invalid plugin: {plugin.PLUGIN_INFO['name']}")
        
        # Проверка зависимостей
        if not await self._check_dependencies(plugin):
            raise DependencyError(f"Missing dependencies for: {plugin.PLUGIN_INFO['name']}")
        
        # Регистрация
        plugin_id = f"{plugin.PLUGIN_INFO['category']}/{plugin.PLUGIN_INFO['name']}"
        self._plugins[plugin_id] = plugin
        
        # Добавление в категорию
        category = plugin.PLUGIN_INFO['category']
        if category not in self._categories:
            self._categories[category] = []
        self._categories[category].append(plugin_id)
        
        # Инициализация
        await plugin.initialize({})
        
        return True
    
    def discover(self, capability: str) -> List[BasePlugin]:
        """
        Поиск плагинов по возможности
        """
        
        matching = []
        for plugin in self._plugins.values():
            if capability in plugin.get_capabilities():
                matching.append(plugin)
        
        return matching
    
    def get_by_category(self, category: str) -> List[BasePlugin]:
        """
        Получение плагинов по категории
        """
        
        plugin_ids = self._categories.get(category, [])
        return [self._plugins[pid] for pid in plugin_ids]
```

## 5.4 Marketplace Templates

```python
class TemplateMarketplace:
    """
    Маркетплейс шаблонов
    """
    
    CATEGORIES = [
        "video_templates",
        "animation_templates",
        "graphics_templates",
        "branding_kits",
        "content_packs",
        "niche_bundles",
        "style_presets",
        "effect_packs"
    ]
    
    async def browse(self, filters: Dict = None) -> List[TemplateItem]:
        """
        Просмотр маркетплейса
        """
        
        query = {}
        
        if filters:
            if filters.get("category"):
                query["category"] = filters["category"]
            if filters.get("niche"):
                query["niche"] = filters["niche"]
            if filters.get("platform"):
                query["platform"] = filters["platform"]
            if filters.get("price_range"):
                query["price"] = {"$gte": filters["price_range"][0], "$lte": filters["price_range"][1]}
            if filters.get("rating_min"):
                query["rating"] = {"$gte": filters["rating_min"]}
        
        templates = await self.db.templates.find(query).sort("popularity", -1).to_list(100)
        
        return [TemplateItem(**t) for t in templates]
    
    async def install(self, template_id: str, user_id: str) -> bool:
        """
        Установка шаблона
        """
        
        template = await self.get_template(template_id)
        
        # Проверка лицензии
        if template.license_type == "paid":
            if not await self.check_purchase(user_id, template_id):
                raise LicenseError("Template not purchased")
        
        # Загрузка ассетов
        assets = await self.download_assets(template)
        
        # Установка в проект пользователя
        await self.install_to_user(user_id, template, assets)
        
        return True
    
    async def publish(self, creator_id: str, template: TemplatePackage) -> str:
        """
        Публикация шаблона в маркетплейс
        """
        
        # Валидация
        validation = await self.validate_template(template)
        
        if not validation.passed:
            raise ValidationError(validation.errors)
        
        # Модерация
        moderation_status = await self.submit_for_moderation(template)
        
        # Создание листинга
        listing = await self.create_listing(creator_id, template, moderation_status)
        
        return listing.id


class TemplateItem:
    """
    Элемент маркетплейса
    """
    
    id: str
    name: str
    description: str
    category: str
    niche: List[str]
    platform: List[str]
    preview_url: str
    demo_video_url: str
    price: float
    license_type: str  # free, paid, subscription
    rating: float
    downloads: int
    creator: CreatorInfo
    tags: List[str]
    variables: List[str]  # Настраиваемые элементы
    requirements: List[str]  # Требуемые плагины
```

## 5.5 Extension API

```python
class ExtensionAPI:
    """
    API для расширений
    """
    
    # Точки расширения
    EXTENSION_POINTS = {
        "pre_process": "Перед обработкой запроса",
        "post_process": "После обработки запроса",
        "pre_render": "Перед рендерингом",
        "post_render": "После рендеринга",
        "on_export": "При экспорте",
        "on_error": "При ошибке",
        "custom_command": "Кастомные команды"
    }
    
    def register_hook(self, extension_point: str, callback: Callable):
        """
        Регистрация хука
        """
        
        if extension_point not in self.EXTENSION_POINTS:
            raise ValueError(f"Unknown extension point: {extension_point}")
        
        self._hooks[extension_point].append(callback)
    
    async def trigger_hook(self, extension_point: str, data: Any) -> Any:
        """
        Вызов хука
        """
        
        result = data
        
        for callback in self._hooks.get(extension_point, []):
            result = await callback(result)
        
        return result
    
    # Доступные сервисы для расширений
    AVAILABLE_SERVICES = {
        "llm": "Доступ к LLM API",
        "image_gen": "Генерация изображений",
        "video_gen": "Генерация видео",
        "tts": "Text-to-Speech",
        "storage": "Хранилище файлов",
        "database": "Доступ к БД (ограниченный)",
        "analytics": "Аналитика",
        "notifications": "Уведомления"
    }
    
    def get_service(self, service_name: str) -> Any:
        """
        Получение сервиса для расширения
        """
        
        if service_name not in self.AVAILABLE_SERVICES:
            raise ServiceNotAvailable(service_name)
        
        return self._services[service_name]
```

## 5.6 Versioning & Compatibility

```python
class VersionManager:
    """
    Управление версиями и совместимостью
    """
    
    COMPATIBILITY_MATRIX = {
        "core_api": {
            "1.0": ["1.0.x", "1.1.x"],
            "2.0": ["2.0.x", "2.1.x", "2.2.x"],
            "3.0": ["3.0.x"]
        },
        "plugin_api": {
            "1.0": ["1.0.x"],
            "2.0": ["2.0.x", "2.1.x"]
        }
    }
    
    def check_compatibility(self, plugin: BasePlugin, core_version: str) -> bool:
        """
        Проверка совместимости плагина
        """
        
        plugin_api_version = plugin.PLUGIN_INFO.get("api_version", "1.0")
        
        compatible_core_versions = self.COMPATIBILITY_MATRIX["plugin_api"].get(plugin_api_version, [])
        
        return any(
            core_version.startswith(v.rstrip('x'))
            for v in compatible_core_versions
        )
    
    async def migrate_plugin(self, plugin: BasePlugin, target_version: str) -> BasePlugin:
        """
        Миграция плагина на новую версию API
        """
        
        current_version = plugin.PLUGIN_INFO.get("api_version")
        
        migration_path = self.get_migration_path(current_version, target_version)
        
        for step in migration_path:
            plugin = await step.migrate(plugin)
        
        return plugin
```
