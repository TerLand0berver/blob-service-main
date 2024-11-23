"""
Image enhancement middleware implementation.
"""
import io
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw, ImageFont
import numpy as np

from .base import BaseMiddleware

class ImageEnhancementMiddleware(BaseMiddleware):
    """Middleware for enhancing images with filters and watermarks."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize image enhancement middleware."""
        super().__init__(config)
        self.watermark_text = self.config.get('watermark_text', '')
        self.watermark_font = self.config.get('watermark_font', 'arial.ttf')
        self.watermark_size = self.config.get('watermark_size', 30)
        self.watermark_opacity = self.config.get('watermark_opacity', 0.5)
        self.watermark_position = self.config.get('watermark_position', 'bottom-right')
        
        self.smart_crop = self.config.get('smart_crop', True)
        self.enhance_colors = self.config.get('enhance_colors', True)
        self.sharpen = self.config.get('sharpen', True)
        self.denoise = self.config.get('denoise', True)
        
        self.color_balance = self.config.get('color_balance', {
            'brightness': 1.0,
            'contrast': 1.1,
            'saturation': 1.1,
            'sharpness': 1.2
        })
    
    async def process_upload(self, file_data: bytes, metadata: Dict[str, Any]) -> Tuple[bytes, Dict[str, Any]]:
        """Process image during upload."""
        try:
            # Skip non-image files
            if not metadata.get('content_type', '').startswith('image/'):
                return file_data, metadata
            
            # Open image
            img = Image.open(io.BytesIO(file_data))
            
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                background.paste(img, mask=img.split()[-1])
                img = background
            elif img.mode not in ('RGB'):
                img = img.convert('RGB')
            
            # Apply smart cropping if enabled
            if self.smart_crop:
                img = self._smart_crop(img)
            
            # Apply color enhancements
            if self.enhance_colors:
                img = self._enhance_colors(img)
            
            # Apply sharpening
            if self.sharpen:
                img = self._sharpen_image(img)
            
            # Apply denoising
            if self.denoise:
                img = self._denoise_image(img)
            
            # Add watermark if configured
            if self.watermark_text:
                img = self._add_watermark(img)
            
            # Save enhanced image
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=95, optimize=True)
            enhanced_data = output.getvalue()
            
            # Update metadata
            metadata['enhanced'] = True
            metadata['enhancements'] = []
            if self.smart_crop:
                metadata['enhancements'].append('smart_crop')
            if self.enhance_colors:
                metadata['enhancements'].append('color_enhancement')
            if self.sharpen:
                metadata['enhancements'].append('sharpening')
            if self.denoise:
                metadata['enhancements'].append('denoising')
            if self.watermark_text:
                metadata['enhancements'].append('watermark')
            
            return enhanced_data, metadata
            
        except Exception as e:
            # Log error but don't fail
            print(f"Image enhancement failed: {e}")
            return file_data, metadata
    
    async def process_download(self, file_data: bytes, metadata: Dict[str, Any]) -> Tuple[bytes, Dict[str, Any]]:
        """Process image during download."""
        # No processing needed during download
        return file_data, metadata
    
    def _smart_crop(self, img: Image.Image) -> Image.Image:
        """Apply smart cropping to focus on the important parts of the image."""
        # Convert to numpy array
        img_array = np.array(img)
        
        # Calculate saliency map (simple edge detection)
        gray = np.dot(img_array[...,:3], [0.2989, 0.5870, 0.1140])
        edges_x = np.gradient(gray, axis=1)
        edges_y = np.gradient(gray, axis=0)
        saliency = np.sqrt(edges_x**2 + edges_y**2)
        
        # Find the region with highest saliency
        window_size = min(img.size) // 2
        max_saliency = float('-inf')
        best_x = best_y = 0
        
        for y in range(0, img.height - window_size, window_size//4):
            for x in range(0, img.width - window_size, window_size//4):
                window_saliency = saliency[y:y+window_size, x:x+window_size].mean()
                if window_saliency > max_saliency:
                    max_saliency = window_saliency
                    best_x, best_y = x, y
        
        # Crop around the most salient region
        return img.crop((
            best_x,
            best_y,
            min(best_x + window_size, img.width),
            min(best_y + window_size, img.height)
        ))
    
    def _enhance_colors(self, img: Image.Image) -> Image.Image:
        """Enhance image colors."""
        enhancers = {
            'brightness': ImageEnhance.Brightness(img),
            'contrast': ImageEnhance.Contrast(img),
            'saturation': ImageEnhance.Color(img),
            'sharpness': ImageEnhance.Sharpness(img)
        }
        
        for name, enhancer in enhancers.items():
            factor = self.color_balance.get(name, 1.0)
            img = enhancer.enhance(factor)
        
        return img
    
    def _sharpen_image(self, img: Image.Image) -> Image.Image:
        """Apply intelligent sharpening."""
        # Create sharpening kernel
        kernel = ImageFilter.UnsharpMask(radius=2, percent=150, threshold=3)
        return img.filter(kernel)
    
    def _denoise_image(self, img: Image.Image) -> Image.Image:
        """Apply noise reduction."""
        # Use median filter for noise reduction
        return img.filter(ImageFilter.MedianFilter(size=3))
    
    def _add_watermark(self, img: Image.Image) -> Image.Image:
        """Add watermark to image."""
        try:
            # Create watermark layer
            watermark = Image.new('RGBA', img.size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(watermark)
            
            # Load font
            try:
                font = ImageFont.truetype(self.watermark_font, self.watermark_size)
            except:
                font = ImageFont.load_default()
            
            # Calculate text size
            text_width = draw.textlength(self.watermark_text, font=font)
            text_height = self.watermark_size
            
            # Calculate position
            padding = 20
            if self.watermark_position == 'bottom-right':
                position = (
                    img.width - text_width - padding,
                    img.height - text_height - padding
                )
            elif self.watermark_position == 'bottom-left':
                position = (
                    padding,
                    img.height - text_height - padding
                )
            elif self.watermark_position == 'top-right':
                position = (
                    img.width - text_width - padding,
                    padding
                )
            elif self.watermark_position == 'top-left':
                position = (padding, padding)
            else:  # center
                position = (
                    (img.width - text_width) / 2,
                    (img.height - text_height) / 2
                )
            
            # Draw watermark
            draw.text(
                position,
                self.watermark_text,
                font=font,
                fill=(255, 255, 255, int(255 * self.watermark_opacity))
            )
            
            # Composite watermark onto image
            return Image.alpha_composite(img.convert('RGBA'), watermark).convert('RGB')
            
        except Exception as e:
            print(f"Watermark application failed: {e}")
            return img
