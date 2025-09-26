from django import forms
from .models import LimiteTransaccion
from clientes.models import Cliente
from monedas.models import Moneda
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

class LimiteTransaccionForm(forms.ModelForm):
    """
    Formulario para crear o editar límites de transacción.
    Basado en el patrón exitoso de TasaDeCambioForm.
    """
    
    # Definir campos explícitamente como en TasaDeCambioForm
    limite_diario = forms.DecimalField(
        max_digits=20,
        decimal_places=8,
        required=True,
        widget=forms.NumberInput(attrs={"step": "any", "class": "form-control custom-input"})
    )
    
    limite_mensual = forms.DecimalField(
        max_digits=20,
        decimal_places=8,
        required=True,
        widget=forms.NumberInput(attrs={"step": "any", "class": "form-control custom-input"})
    )
    
    class Meta:
        model = LimiteTransaccion
        fields = ['cliente', 'moneda', 'limite_diario', 'limite_mensual']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control custom-input'}),
            'moneda': forms.Select(attrs={'class': 'form-control custom-input'}),
        }

    def __init__(self, *args, **kwargs):
        """Inicialización personalizada: crear choices dinámicos para clientes y monedas"""
        super().__init__(*args, **kwargs)
        
        # Clientes activos
        clientes = Cliente.objects.filter(estado='activo')
        cliente_choices = [('', 'Seleccione un cliente...')]
        cliente_choices += [(c.id, c.nombre) for c in clientes]
        self.fields['cliente'].widget.choices = cliente_choices
        
        # Monedas activas
        monedas = Moneda.objects.filter(estado=True)
        moneda_choices = [('', 'Seleccione una moneda...')]
        moneda_choices += [(m.id, f"{m.nombre} ({m.abreviacion})") for m in monedas]
        self.fields['moneda'].widget.choices = moneda_choices

    def clean_limite_diario(self):
        """Validación simple del límite diario"""
        valor = self.cleaned_data.get('limite_diario')
        
        print(f"🔍 DEBUG clean_limite_diario:")
        print(f"   - Valor recibido: {valor} (tipo: {type(valor)})")
        print(f"   - Datos POST: limite_diario = '{self.data.get('limite_diario')}'")
        
        # Si ya es un Decimal válido, solo validar que sea >= 0
        if isinstance(valor, Decimal):
            if valor < 0:
                raise forms.ValidationError("El límite diario debe ser mayor o igual a 0")
            return valor
        
        # Si es None, verificar en datos POST
        raw_value = self.data.get('limite_diario', '')
        print(f"   - Raw value: '{raw_value}'")
        
        if not raw_value or raw_value.strip() == '':
            raise forms.ValidationError("El límite diario es requerido")
        
        # Intentar convertir manualmente
        try:
            # Reemplazar coma por punto si es necesario
            clean_value = str(raw_value).replace(',', '.')
            decimal_value = Decimal(clean_value)
            
            if decimal_value < 0:
                raise forms.ValidationError("El límite diario debe ser mayor o igual a 0")
                
            print(f"   - Valor convertido: {decimal_value}")
            return decimal_value
            
        except (InvalidOperation, ValueError) as e:
            print(f"   - Error de conversión: {e}")
            raise forms.ValidationError(f"Valor inválido para límite diario: '{raw_value}'")

    def clean_limite_mensual(self):
        """Validación simple del límite mensual"""
        valor = self.cleaned_data.get('limite_mensual')
        
        print(f"🔍 DEBUG clean_limite_mensual:")
        print(f"   - Valor recibido: {valor} (tipo: {type(valor)})")
        print(f"   - Datos POST: limite_mensual = '{self.data.get('limite_mensual')}'")
        
        # Si ya es un Decimal válido, solo validar que sea >= 0
        if isinstance(valor, Decimal):
            if valor < 0:
                raise forms.ValidationError("El límite mensual debe ser mayor o igual a 0")
            return valor
        
        # Si es None, verificar en datos POST
        raw_value = self.data.get('limite_mensual', '')
        print(f"   - Raw value: '{raw_value}'")
        
        if not raw_value or raw_value.strip() == '':
            raise forms.ValidationError("El límite mensual es requerido")
        
        # Intentar convertir manualmente
        try:
            # Reemplazar coma por punto si es necesario
            clean_value = str(raw_value).replace(',', '.')
            decimal_value = Decimal(clean_value)
            
            if decimal_value < 0:
                raise forms.ValidationError("El límite mensual debe ser mayor o igual a 0")
                
            print(f"   - Valor convertido: {decimal_value}")
            return decimal_value
            
        except (InvalidOperation, ValueError) as e:
            print(f"   - Error de conversión: {e}")
            raise forms.ValidationError(f"Valor inválido para límite mensual: '{raw_value}'")

    def clean(self):
        """Validación de consistencia entre límites diario y mensual"""
        cleaned_data = super().clean()
        limite_diario = cleaned_data.get('limite_diario')
        limite_mensual = cleaned_data.get('limite_mensual')
        
        print(f"🔍 DEBUG clean (validación final):")
        print(f"   - Límite diario: {limite_diario}")
        print(f"   - Límite mensual: {limite_mensual}")
        
        if limite_diario and limite_mensual:
            if limite_mensual < limite_diario:
                raise forms.ValidationError("El límite mensual no puede ser menor al límite diario.")
        
        return cleaned_data